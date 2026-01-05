const { autoUpdater } = require('electron-updater');
const { dialog } = require('electron');
const log = require('electron-log');

class UpdateManager {
  constructor(windowManager) {
    this.windowManager = windowManager;
    this.isDev = process.env.NODE_ENV === 'development';
    this.updateCheckInterval = null;
    this.updateCheckIntervalMs = 1000 * 60 * 60 * 6; // 6小时检查一次
    
    // 配置日志
    this.setupLogging();
    
    // 仅在非开发模式下启用自动更新
    if (!this.isDev) {
      this.setupAutoUpdater();
      this.startUpdateChecks();
    }
  }

  /**
   * 设置日志记录
   */
  setupLogging() {
    // 设置日志文件位置
    log.transports.file.level = 'info';
    log.transports.file.format = '{y}-{m}-{d} {h}:{mi}:{s} [{level}] {text}';
    log.transports.file.maxSize = 10 * 1024 * 1024; // 10MB
    
    // 开发模式下同时输出到控制台
    if (this.isDev) {
      log.transports.console.level = 'debug';
    }
  }

  /**
   * 配置自动更新器
   */
  setupAutoUpdater() {
    // 配置更新服务器URL
    autoUpdater.setFeedURL({
      provider: 'github',
      owner: 'your-username',
      repo: 'py-copilot-desktop'
    });

    // 配置更新选项
    autoUpdater.autoDownload = false; // 不自动下载更新
    autoUpdater.autoInstallOnAppQuit = true; // 应用退出时自动安装更新

    // 设置事件监听器
    this.setupEventListeners();

    // 设置更新检查器
    if (this.updateCheckIntervalMs > 0) {
      this.updateCheckInterval = setInterval(() => {
        this.checkForUpdates(true);
      }, this.updateCheckIntervalMs);
    }
  }

  /**
   * 设置事件监听器
   */
  setupEventListeners() {
    // 检查更新错误
    autoUpdater.on('error', (error) => {
      log.error('更新检查失败:', error);
      this.notifyRenderer('update-error', { message: error.message });
    });

    // 检查是否有可用更新
    autoUpdater.on('checking-for-update', () => {
      log.info('检查更新中...');
      this.notifyRenderer('checking-for-update');
    });

    // 找到可用的更新
    autoUpdater.on('update-available', (info) => {
      log.info('发现可用更新:', info);
      this.showUpdateDialog('available', info);
      this.notifyRenderer('update-available', info);
    });

    // 没有可用更新
    autoUpdater.on('update-not-available', (info) => {
      log.info('没有可用更新:', info);
      this.notifyRenderer('update-not-available', info);
    });

    // 下载进度
    autoUpdater.on('download-progress', (progressObj) => {
      const log_message = `下载进度: ${progressObj.percent.toFixed(2)}% (${progressObj.transferred}/${progressObj.total})`;
      log.info(log_message);
      this.notifyRenderer('download-progress', progressObj);
    });

    // 下载完成
    autoUpdater.on('update-downloaded', (info) => {
      log.info('更新下载完成:', info);
      this.showUpdateDialog('downloaded', info);
      this.notifyRenderer('update-downloaded', info);
    });
  }

  /**
   * 启动更新检查
   */
  startUpdateChecks() {
    // 延迟启动更新检查
    setTimeout(() => {
      this.checkForUpdates(false);
    }, 5000);
  }

  /**
   * 检查更新
   */
  async checkForUpdates(showNoUpdateDialog = false) {
    if (this.isDev) {
      log.info('开发模式下跳过更新检查');
      return;
    }

    try {
      await autoUpdater.checkForUpdatesAndReport();
    } catch (error) {
      log.error('检查更新失败:', error);
      
      if (showNoUpdateDialog) {
        this.showErrorDialog('检查更新失败', error.message);
      }
    }
  }

  /**
   * 下载更新
   */
  async downloadUpdate() {
    if (this.isDev) {
      log.info('开发模式下跳过更新下载');
      return;
    }

    try {
      await autoUpdater.downloadUpdate();
    } catch (error) {
      log.error('下载更新失败:', error);
      this.showErrorDialog('下载更新失败', error.message);
    }
  }

  /**
   * 安装更新
   */
  installUpdate() {
    if (this.isDev) {
      log.info('开发模式下跳过更新安装');
      return;
    }

    autoUpdater.quitAndInstall();
  }

  /**
   * 显示更新对话框
   */
  showUpdateDialog(type, info) {
    const mainWindow = this.windowManager.getMainWindow();
    if (!mainWindow) return;

    switch (type) {
      case 'available':
        dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: '发现新版本',
          message: `发现新版本 v${info.version}`,
          detail: '是否立即下载并安装更新？',
          buttons: ['立即下载', '稍后提醒', '跳过此版本'],
          defaultId: 0,
          cancelId: 1
        }).then((result) => {
          switch (result.response) {
            case 0: // 立即下载
              this.downloadUpdate();
              break;
            case 2: // 跳过此版本
              this.skipCurrentVersion(info.version);
              break;
            default:
              // 稍后提醒
              break;
          }
        });
        break;

      case 'downloaded':
        dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: '更新准备就绪',
          message: `v${info.version} 已下载完成`,
          detail: '是否立即重启应用并安装更新？',
          buttons: ['立即重启', '稍后重启'],
          defaultId: 0,
          cancelId: 1
        }).then((result) => {
          if (result.response === 0) {
            this.installUpdate();
          }
        });
        break;
    }
  }

  /**
   * 显示错误对话框
   */
  showErrorDialog(title, message) {
    const mainWindow = this.windowManager.getMainWindow();
    if (!mainWindow) return;

    dialog.showMessageBox(mainWindow, {
      type: 'error',
      title,
      message,
      buttons: ['确定']
    });
  }

  /**
   * 跳过当前版本
   */
  skipCurrentVersion(version) {
    const Store = require('electron-store');
    const store = new Store();
    store.set('skippedVersions', [...(store.get('skippedVersions') || []), version]);
  }

  /**
   * 通知渲染进程
   */
  notifyRenderer(event, data) {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.webContents.send('update-event', { event, data });
    }
  }

  /**
   * 获取当前版本
   */
  getCurrentVersion() {
    return autoUpdater.currentVersion || require('../package.json').version;
  }

  /**
   * 清理资源
   */
  cleanup() {
    if (this.updateCheckInterval) {
      clearInterval(this.updateCheckInterval);
      this.updateCheckInterval = null;
    }
  }
}

module.exports = UpdateManager;