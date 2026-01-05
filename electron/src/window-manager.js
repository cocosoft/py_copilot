const { BrowserWindow } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

class WindowManager {
  constructor() {
    this.windows = new Map();
    this.mainWindow = null;
    this.defaultOptions = {
      width: 1400,
      height: 900,
      minWidth: 800,
      minHeight: 600,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, '../preload.js'),
        webSecurity: true,
        allowRunningInsecureContent: false,
        experimentalFeatures: false,
      },
      show: false,
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    };
  }

  /**
   * 创建主窗口
   */
  createMainWindow() {
    const options = {
      ...this.defaultOptions,
      width: 1400,
      height: 900,
      icon: path.join(__dirname, '../frontend/public/app-logo.png'),
      title: 'Py Copilot',
    };

    this.mainWindow = new BrowserWindow(options);
    this.windows.set('main', this.mainWindow);

    // 加载应用
    if (isDev) {
      this.mainWindow.loadURL('http://localhost:5173');
      this.mainWindow.webContents.openDevTools();
    } else {
      this.mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
    }

    // 窗口事件处理
    this.setupMainWindowEvents();

    return this.mainWindow;
  }

  /**
   * 设置主窗口事件
   */
  setupMainWindowEvents() {
    if (!this.mainWindow) return;

    // 准备显示时
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow.show();
      
      if (isDev) {
        this.mainWindow.webContents.openDevTools();
      }
    });

    // 页面加载错误
    this.mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
      console.error('页面加载失败:', errorDescription, validatedURL);
    });

    // 渲染进程崩溃
    this.mainWindow.webContents.on('render-process-gone', (event, details) => {
      console.error('渲染进程崩溃:', details);
    });

    // 外部链接处理
    this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      const { shell } = require('electron');
      shell.openExternal(url);
      return { action: 'deny' };
    });
  }

  /**
   * 创建模态窗口
   */
  createModalWindow(options = {}) {
    const modalOptions = {
      ...this.defaultOptions,
      width: options.width || 800,
      height: options.height || 600,
      parent: this.mainWindow,
      modal: true,
      resizable: options.resizable !== false,
      minimizable: false,
      maximizable: false,
      closable: true,
      title: options.title || '模态窗口',
      ...options,
    };

    const modal = new BrowserWindow(modalOptions);
    
    if (options.url) {
      modal.loadURL(options.url);
    } else if (options.html) {
      modal.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(options.html)}`);
    } else {
      // 默认内容
      modal.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
    }

    this.windows.set(`modal-${Date.now()}`, modal);

    modal.on('closed', () => {
      this.windows.delete(modal.id);
    });

    return modal;
  }

  /**
   * 创建工具窗口
   */
  createToolWindow(options = {}) {
    const toolOptions = {
      ...this.defaultOptions,
      width: options.width || 400,
      height: options.height || 300,
      x: options.x,
      y: options.y,
      frame: options.frame !== false,
      transparent: options.transparent || false,
      alwaysOnTop: options.alwaysOnTop || false,
      skipTaskbar: options.skipTaskbar || false,
      title: options.title || '工具窗口',
      ...options,
    };

    const tool = new BrowserWindow(toolOptions);
    
    if (options.url) {
      tool.loadURL(options.url);
    } else if (options.html) {
      tool.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(options.html)}`);
    }

    this.windows.set(`tool-${Date.now()}`, tool);

    tool.on('closed', () => {
      this.windows.delete(tool.id);
    });

    return tool;
  }

  /**
   * 获取窗口
   */
  getWindow(key) {
    if (key === 'main') {
      return this.mainWindow;
    }
    return this.windows.get(key);
  }

  /**
   * 关闭所有窗口
   */
  closeAll() {
    this.windows.forEach((window, key) => {
      if (!window.isDestroyed()) {
        window.close();
      }
    });
    this.windows.clear();
  }

  /**
   * 显示/隐藏窗口
   */
  showWindow(key) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      window.show();
    }
  }

  hideWindow(key) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      window.hide();
    }
  }

  /**
   * 最小化/最大化窗口
   */
  minimizeWindow(key) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      window.minimize();
    }
  }

  maximizeWindow(key) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      if (window.isMaximized()) {
        window.unmaximize();
      } else {
        window.maximize();
      }
    }
  }

  /**
   * 设置窗口属性
   */
  setWindowProperty(key, property, value) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      window[property] = value;
    }
  }

  /**
   * 获取窗口状态
   */
  getWindowState(key) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      return {
        isVisible: window.isVisible(),
        isMaximized: window.isMaximized(),
        isMinimized: window.isMinimized(),
        isFocused: window.isFocused(),
        getBounds: window.getBounds(),
        getSize: window.getSize(),
        getPosition: window.getPosition(),
      };
    }
    return null;
  }

  /**
   * 广播消息到所有窗口
   */
  broadcast(channel, data) {
    this.windows.forEach((window) => {
      if (window.webContents && !window.isDestroyed()) {
        window.webContents.send(channel, data);
      }
    });
  }

  /**
   * 重新加载窗口
   */
  reload(key) {
    const window = this.getWindow(key);
    if (window && !window.webContents && !window.isDestroyed()) {
      window.webContents.reload();
    }
  }

  /**
   * 强制重新加载窗口
   */
  forceReload(key) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      window.webContents.reloadIgnoringCache();
    }
  }

  /**
   * 打开开发者工具
   */
  openDevTools(key) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      window.webContents.openDevTools();
    }
  }

  /**
   * 关闭开发者工具
   */
  closeDevTools(key) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      window.webContents.closeDevTools();
    }
  }

  /**
   * 截图
   */
  capture(key) {
    return new Promise((resolve, reject) => {
      const window = this.getWindow(key);
      if (window && !window.isDestroyed()) {
        window.webContents.capturePage().then((image) => {
          resolve(image.toDataURL());
        }).catch(reject);
      } else {
        reject(new Error('Window not found'));
      }
    });
  }

  /**
   * 打印
   */
  print(key, options = {}) {
    const window = this.getWindow(key);
    if (window && !window.isDestroyed()) {
      window.webContents.print(options);
    }
  }

  /**
   * 导出PDF
   */
  exportToPDF(key, options = {}) {
    return new Promise((resolve, reject) => {
      const window = this.getWindow(key);
      if (window && !window.isDestroyed()) {
        const pdfOptions = {
          printBackground: true,
          marginsType: 1,
          printSelectionOnly: false,
          landscape: false,
          ...options,
        };

        window.webContents.printToPDF(pdfOptions)
          .then(data => resolve(data))
          .catch(reject);
      } else {
        reject(new Error('Window not found'));
      }
    });
  }
}

module.exports = WindowManager;