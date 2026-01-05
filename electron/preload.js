const { contextBridge, ipcRenderer } = require('electron');

// 安全地暴露API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 文件操作
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (defaultPath, content) => ipcRenderer.invoke('dialog:saveFile', defaultPath, content),

  // 系统信息
  getSystemInfo: () => ipcRenderer.invoke('system:getInfo'),

  // 应用程序
  getAppVersion: () => ipcRenderer.invoke('app:getVersion'),
  setBadge: (text) => ipcRenderer.invoke('app:setBadge', text),

  // 窗口控制
  minimizeWindow: () => ipcRenderer.invoke('window:minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window:maximize'),
  closeWindow: () => ipcRenderer.invoke('window:close'),

  // 剪贴板
  writeClipboardText: (text) => ipcRenderer.invoke('clipboard:writeText', text),
  readClipboardText: () => ipcRenderer.invoke('clipboard:readText'),

  // 通知
  showNotification: (options) => ipcRenderer.invoke('notification:show', options),

  // 监听菜单事件
  onMenuAction: (callback) => {
    ipcRenderer.on('menu-new', callback);
    ipcRenderer.on('menu-open-file', (event, filePath) => callback('menu-open-file', filePath));
    ipcRenderer.on('menu-save', callback);
    ipcRenderer.on('menu-export-pdf', callback);
    ipcRenderer.on('menu-export-image', callback);
    ipcRenderer.on('menu-check-updates', callback);
  },

  // 移除监听器
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  },

  // 版本信息
  versions: {
    node: () => process.versions.node,
    chrome: () => process.versions.chrome,
    electron: () => process.versions.electron
  },

  // 平台信息
  platform: process.platform,

  // 事件监听
  on: (channel, callback) => {
    // 允许特定的频道
    const validChannels = [
      'window-blurred',
      'window-focused',
      'app-ready',
      'update-available'
    ];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, callback);
    }
  },

  // 一次性事件监听
  once: (channel, callback) => {
    const validChannels = [
      'app-ready',
      'window-ready'
    ];
    if (validChannels.includes(channel)) {
      ipcRenderer.once(channel, callback);
    }
  },

  // 发送消息到主进程
  send: (channel, data) => {
    const validChannels = [
      'window-ready',
      'request-update-check'
    ];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },

  // 文件系统路径
  paths: {
    userData: () => ipcRenderer.invoke('app:getPath', 'userData'),
    documents: () => ipcRenderer.invoke('app:getPath', 'documents')
  },

  // 快捷键支持
  registerGlobalShortcut: (accelerator, callback) => {
    return ipcRenderer.invoke('shortcut:register', accelerator, callback);
  },

  // 对话框
  showMessageBox: (options) => {
    return ipcRenderer.invoke('dialog:showMessageBox', options);
  },

  showErrorBox: (title, content) => {
    return ipcRenderer.invoke('dialog:showErrorBox', title, content);
  },

  // 浏览器窗口
  createWindow: (options) => {
    return ipcRenderer.invoke('window:create', options);
  },

  // 打印
  print: (options) => {
    return ipcRenderer.invoke('print:show', options);
  },

  printToPDF: (options) => {
    return ipcRenderer.invoke('print:toPDF', options);
  },

  // 自动更新
  checkForUpdates: () => {
    return ipcRenderer.invoke('updater:check');
  },

  // 启动时最小化到托盘
  startInTray: () => {
    return ipcRenderer.invoke('tray:start');
  }
});

// 开发环境下的额外API
if (process.env.NODE_ENV === 'development') {
  contextBridge.exposeInMainWorld('devAPI', {
    reloadWindow: () => ipcRenderer.send('window:reload'),
    toggleDevTools: () => ipcRenderer.send('window:toggleDevTools'),
    openDevTools: () => ipcRenderer.send('window:openDevTools'),
    closeDevTools: () => ipcRenderer.send('window:closeDevTools'),
    inspectElement: (x, y) => ipcRenderer.send('window:inspectElement', x, y)
  });
}