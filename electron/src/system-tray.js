const { Tray, Menu, nativeImage } = require('electron');
const path = require('path');

class SystemTray {
  constructor(windowManager) {
    this.windowManager = windowManager;
    this.tray = null;
    this.isDev = process.env.NODE_ENV === 'development';
    this.init();
  }

  /**
   * 初始化系统托盘
   */
  init() {
    if (this.isDev) {
      console.log('开发模式下跳过系统托盘初始化');
      return;
    }

    // 创建托盘图标
    const iconPath = path.join(__dirname, '../icons/tray-icon.png');
    const icon = nativeImage.createFromPath(iconPath);
    
    // 如果图标文件不存在，创建默认图标
    let trayIcon = icon;
    if (icon.isEmpty()) {
      // 创建默认图标
      trayIcon = nativeImage.createFromNamedImage('NSApplicationIcon');
      // 调整图标大小
      trayIcon = trayIcon.resize({ width: 16, height: 16 });
    }

    this.tray = new Tray(trayIcon);
    this.tray.setToolTip('Py Copilot');
    this.setupContextMenu();
    this.setupEventListeners();
  }

  /**
   * 设置右键菜单
   */
  setupContextMenu() {
    const contextMenu = Menu.buildFromTemplate([
      {
        label: '显示窗口',
        click: () => {
          this.showMainWindow();
        }
      },
      {
        label: '隐藏到托盘',
        click: () => {
          this.hideToTray();
        }
      },
      { type: 'separator' },
      {
        label: '偏好设置',
        click: () => {
          this.openPreferences();
        }
      },
      {
        label: '检查更新',
        click: () => {
          this.checkForUpdates();
        }
      },
      { type: 'separator' },
      {
        label: '退出',
        click: () => {
          this.quit();
        }
      }
    ]);

    this.tray.setContextMenu(contextMenu);
  }

  /**
   * 设置事件监听器
   */
  setupEventListeners() {
    // 双击托盘图标显示主窗口
    this.tray.on('double-click', () => {
      this.showMainWindow();
    });

    // 左键点击
    this.tray.on('click', (event, bounds) => {
      if (event.shiftKey) {
        // Shift+左键显示上下文菜单
        this.tray.popUpContextMenu();
      } else {
        // 普通左键切换窗口显示/隐藏
        this.toggleWindow();
      }
    });

    // 右键显示上下文菜单
    this.tray.on('right-click', () => {
      this.tray.popUpContextMenu();
    });
  }

  /**
   * 显示主窗口
   */
  showMainWindow() {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore();
      }
      mainWindow.show();
      mainWindow.focus();
    }
  }

  /**
   * 隐藏到托盘
   */
  hideToTray() {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.hide();
    }
  }

  /**
   * 切换窗口显示状态
   */
  toggleWindow() {
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      if (mainWindow.isVisible() && !mainWindow.isMinimized()) {
        this.hideToTray();
      } else {
        this.showMainWindow();
      }
    }
  }

  /**
   * 打开偏好设置
   */
  openPreferences() {
    this.showMainWindow();
    // 向渲染进程发送消息打开设置页面
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.webContents.send('open-preferences');
    }
  }

  /**
   * 检查更新
   */
  checkForUpdates() {
    this.showMainWindow();
    // 向渲染进程发送消息检查更新
    const mainWindow = this.windowManager.getMainWindow();
    if (mainWindow) {
      mainWindow.webContents.send('check-updates');
    }
  }

  /**
   * 退出应用
   */
  quit() {
    // 清理资源
    this.cleanup();
    
    // 退出应用
    const { app } = require('electron');
    app.quit();
  }

  /**
   * 显示通知
   */
  showNotification(title, message, options = {}) {
    const { Notification } = require('electron');
    
    if (Notification.isSupported()) {
      const notification = new Notification({
        title,
        body: message,
        icon: path.join(__dirname, '../icons/tray-icon.png'),
        ...options
      });

      notification.on('click', () => {
        this.showMainWindow();
      });

      notification.show();
    }
  }

  /**
   * 设置托盘图标状态
   */
  setIconState(state, iconPath) {
    if (this.tray) {
      const icon = nativeImage.createFromPath(iconPath);
      if (!icon.isEmpty()) {
        this.tray.setImage(icon);
      }
    }
  }

  /**
   * 更新托盘提示
   */
  setToolTip(tooltip) {
    if (this.tray) {
      this.tray.setToolTip(tooltip);
    }
  }

  /**
   * 销毁托盘
   */
  destroy() {
    if (this.tray) {
      this.tray.destroy();
      this.tray = null;
    }
  }

  /**
   * 清理资源
   */
  cleanup() {
    this.destroy();
  }
}

module.exports = SystemTray;