const log = require('electron-log');

class IPCManager {
  constructor(windowManager) {
    this.windowManager = windowManager;
    this.channels = new Map();
    this.setupDefaultChannels();
  }

  /**
   * 设置默认的IPC通道
   */
  setupDefaultChannels() {
    // 文件操作相关通道
    this.register('dialog:openFile', this.handleOpenFile.bind(this));
    this.register('dialog:saveFile', this.handleSaveFile.bind(this));
    this.register('dialog:openDirectory', this.handleOpenDirectory.bind(this));

    // 系统信息相关通道
    this.register('system:getInfo', this.handleGetSystemInfo.bind(this));
    this.register('system:getEnvironment', this.handleGetEnvironment.bind(this));

    // 应用相关通道
    this.register('app:getVersion', this.handleGetVersion.bind(this));
    this.register('app:setBadge', this.handleSetBadge.bind(this));
    this.register('app:getConfig', this.handleGetConfig.bind(this));
    this.register('app:setConfig', this.handleSetConfig.bind(this));

    // 窗口控制相关通道
    this.register('window:minimize', this.handleMinimizeWindow.bind(this));
    this.register('window:maximize', this.handleMaximizeWindow.bind(this));
    this.register('window:close', this.handleCloseWindow.bind(this));
    this.register('window:restore', this.handleRestoreWindow.bind(this));
    this.register('window:isMaximized', this.handleIsMaximized.bind(this));
    this.register('window:setSize', this.handleSetWindowSize.bind(this));
    this.register('window:center', this.handleCenterWindow.bind(this));

    // 文件系统相关通道
    this.register('fs:readFile', this.handleReadFile.bind(this));
    this.register('fs:writeFile', this.handleWriteFile.bind(this));
    this.register('fs:exists', this.handleFileExists.bind(this));
    this.register('fs:createDirectory', this.handleCreateDirectory.bind(this));
    this.register('fs:getDirectoryContents', this.handleGetDirectoryContents.bind(this));

    // 通知相关通道
    this.register('notification:show', this.handleShowNotification.bind(this));

    // 剪贴板相关通道
    this.register('clipboard:readText', this.handleReadClipboard.bind(this));
    this.register('clipboard:writeText', this.handleWriteClipboard.bind(this));
  }

  /**
   * 注册IPC通道
   */
  register(channel, handler) {
    this.channels.set(channel, handler);
  }

  /**
   * 获取注册的通道列表
   */
  getRegisteredChannels() {
    return Array.from(this.channels.keys());
  }

  /**
   * 设置IPC监听器
   */
  setupIPCHandlers(ipcMain) {
    this.ipcMain = ipcMain;
    
    // 为所有注册的通道设置监听器
    for (const [channel, handler] of this.channels) {
      ipcMain.handle(channel, async (event, ...args) => {
        try {
          log.debug(`IPC请求: ${channel}`, { args, sender: event.sender.id });
          
          // 验证窗口权限
          if (!this.validateWindow(event.sender)) {
            throw new Error('无权访问此功能');
          }

          const result = await handler(event, ...args);
          log.debug(`IPC响应: ${channel}`, { result });
          return result;
        } catch (error) {
          log.error(`IPC错误: ${channel}`, { error: error.message, stack: error.stack });
          throw error;
        }
      });

      // 监听事件（非请求-响应模式）
      ipcMain.on(channel, (event, ...args) => {
        try {
          if (!this.validateWindow(event.sender)) {
            return;
          }

          handler(event, ...args);
        } catch (error) {
          log.error(`IPC事件错误: ${channel}`, { error: error.message });
        }
      });
    }
  }

  /**
   * 验证窗口权限
   */
  validateWindow(sender) {
    // 验证请求是否来自有效窗口
    const windows = this.windowManager.getAllWindows();
    for (const window of windows) {
      if (window.webContents.id === sender.id) {
        return true;
      }
    }
    return false;
  }

  /**
   * 向渲染进程发送消息
   */
  sendToRenderer(channel, data) {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.webContents.send(channel, data);
    }
  }

  /**
   * 向所有窗口发送消息
   */
  sendToAllRenderers(channel, data) {
    const windows = this.windowManager.getAllWindows();
    for (const window of windows) {
      window.webContents.send(channel, data);
    }
  }

  // ===== 文件操作处理方法 =====
  async handleOpenFile(event) {
    const { dialog } = require('electron');
    const result = await dialog.showOpenDialog({
      properties: ['openFile'],
      filters: [
        { name: '所有支持的文件', extensions: ['*'] },
        { name: '文本文件', extensions: ['txt', 'md', 'json', 'csv'] },
        { name: '代码文件', extensions: ['py', 'js', 'ts', 'jsx', 'tsx'] },
        { name: '文档文件', extensions: ['pdf', 'doc', 'docx'] }
      ]
    });
    return result;
  }

  async handleSaveFile(event, defaultPath, content) {
    const { dialog } = require('electron');
    const result = await dialog.showSaveDialog({
      defaultPath,
      filters: [
        { name: '所有支持的文件', extensions: ['*'] },
        { name: '文本文件', extensions: ['txt', 'md', 'json'] },
        { name: '代码文件', extensions: ['py', 'js', 'ts'] }
      ]
    });
    
    if (!result.canceled && result.filePath) {
      const fs = require('fs').promises;
      await fs.writeFile(result.filePath, content, 'utf8');
    }
    
    return result;
  }

  async handleOpenDirectory(event) {
    const { dialog } = require('electron');
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory']
    });
    return result;
  }

  // ===== 系统信息处理方法 =====
  async handleGetSystemInfo(event) {
    const os = require('os');
    return {
      platform: os.platform(),
      arch: os.arch(),
      release: os.release(),
      hostname: os.hostname(),
      cpus: os.cpus().length,
      totalMemory: os.totalmem(),
      freeMemory: os.freemem(),
      uptime: os.uptime()
    };
  }

  async handleGetEnvironment(event) {
    return {
      nodeEnv: process.env.NODE_ENV,
      platform: process.platform,
      arch: process.arch,
      versions: process.versions
    };
  }

  // ===== 应用处理方法 =====
  async handleGetVersion(event) {
    const { app } = require('electron');
    return app.getVersion();
  }

  async handleSetBadge(event, text) {
    const { app } = require('electron');
    if (app.setBadgeCount) {
      app.setBadgeCount(text ? parseInt(text) : 0);
    }
    return true;
  }

  async handleGetConfig(event, key) {
    const appConfig = require('./app-config');
    return appConfig.get(key);
  }

  async handleSetConfig(event, key, value) {
    const appConfig = require('./app-config');
    appConfig.set(key, value);
    return true;
  }

  // ===== 窗口处理方法 =====
  async handleMinimizeWindow(event) {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.minimize();
    }
    return true;
  }

  async handleMaximizeWindow(event) {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      if (mainWindow.isMaximized()) {
        mainWindow.unmaximize();
      } else {
        mainWindow.maximize();
      }
    }
    return true;
  }

  async handleCloseWindow(event) {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.close();
    }
    return true;
  }

  async handleRestoreWindow(event) {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
    return true;
  }

  async handleIsMaximized(event) {
    const mainWindow = this.windowManager.getMainWindow();
    return mainWindow ? mainWindow.isMaximized() : false;
  }

  async handleSetWindowSize(event, width, height) {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.setSize(width, height);
    }
    return true;
  }

  async handleCenterWindow(event) {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.center();
    }
    return true;
  }

  // ===== 文件系统处理方法 =====
  async handleReadFile(event, filePath) {
    const fs = require('fs').promises;
    return await fs.readFile(filePath, 'utf8');
  }

  async handleWriteFile(event, filePath, content) {
    const fs = require('fs').promises;
    await fs.writeFile(filePath, content, 'utf8');
    return true;
  }

  async handleFileExists(event, filePath) {
    const fs = require('fs').promises;
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async handleCreateDirectory(event, dirPath) {
    const fs = require('fs').promises;
    await fs.mkdir(dirPath, { recursive: true });
    return true;
  }

  async handleGetDirectoryContents(event, dirPath) {
    const fs = require('fs').promises;
    const files = await fs.readdir(dirPath);
    const fileStats = await Promise.all(
      files.map(async (file) => {
        const fullPath = require('path').join(dirPath, file);
        const stats = await fs.stat(fullPath);
        return {
          name: file,
          path: fullPath,
          isDirectory: stats.isDirectory(),
          size: stats.size,
          modified: stats.mtime
        };
      })
    );
    return fileStats;
  }

  // ===== 通知处理方法 =====
  async handleShowNotification(event, title, body, options) {
    const { Notification } = require('electron');
    if (Notification.isSupported()) {
      const notification = new Notification({
        title,
        body,
        ...options
      });
      notification.show();
    }
    return true;
  }

  // ===== 剪贴板处理方法 =====
  async handleReadClipboard(event) {
    const { clipboard } = require('electron');
    return clipboard.readText();
  }

  async handleWriteClipboard(event, text) {
    const { clipboard } = require('electron');
    clipboard.writeText(text);
    return true;
  }

  /**
   * 清理资源
   */
  cleanup() {
    this.channels.clear();
  }
}

module.exports = IPCManager;