const { Menu, app, dialog } = require('electron');
const path = require('path');

class MenuManager {
  constructor(windowManager) {
    this.windowManager = windowManager;
    this.template = null;
    this.buildDefaultTemplate();
  }

  /**
   * 构建默认菜单模板
   */
  buildDefaultTemplate() {
    this.template = [
      ...(process.platform === 'darwin' ? [{
        label: app.getName(),
        submenu: [
          { role: 'about', label: '关于 Py Copilot' },
          { type: 'separator' },
          {
            label: '首选项...',
            accelerator: 'CmdOrCtrl+,',
            click: () => {
              this.showPreferences();
            }
          },
          { type: 'separator' },
          { role: 'services', label: '服务' },
          { type: 'separator' },
          { role: 'hide', label: '隐藏 Py Copilot' },
          { role: 'hideothers', label: '隐藏其他' },
          { role: 'unhide', label: '显示全部' },
          { type: 'separator' },
          { role: 'quit', label: '退出 Py Copilot' }
        ]
      }] : []),
      {
        label: '文件',
        submenu: [
          {
            label: '新建',
            accelerator: 'CmdOrCtrl+N',
            click: () => {
              this.broadcastToRenderer('menu-new');
            }
          },
          {
            label: '打开...',
            accelerator: 'CmdOrCtrl+O',
            click: async () => {
              await this.handleOpenFile();
            }
          },
          {
            label: '打开最近文件',
            role: 'recentdocuments',
            submenu: [
              {
                label: '清除最近文件',
                role: 'clearrecentdocuments'
              }
            ]
          },
          { type: 'separator' },
          {
            label: '关闭',
            accelerator: 'CmdOrCtrl+W',
            click: () => {
              this.windowManager.hideWindow('main');
            }
          },
          {
            label: '保存',
            accelerator: 'CmdOrCtrl+S',
            click: () => {
              this.broadcastToRenderer('menu-save');
            }
          },
          {
            label: '另存为...',
            accelerator: 'CmdOrCtrl+Shift+S',
            click: () => {
              this.broadcastToRenderer('menu-save-as');
            }
          },
          { type: 'separator' },
          {
            label: '导入',
            submenu: [
              {
                label: '从文件导入...',
                click: () => {
                  this.broadcastToRenderer('menu-import-file');
                }
              },
              {
                label: '从剪贴板导入',
                click: () => {
                  this.broadcastToRenderer('menu-import-clipboard');
                }
              }
            ]
          },
          {
            label: '导出',
            submenu: [
              {
                label: '导出为 PDF',
                click: () => {
                  this.broadcastToRenderer('menu-export-pdf');
                }
              },
              {
                label: '导出为图片',
                click: () => {
                  this.broadcastToRenderer('menu-export-image');
                }
              },
              {
                label: '导出为文本',
                click: () => {
                  this.broadcastToRenderer('menu-export-text');
                }
              }
            ]
          },
          { type: 'separator' },
          {
            label: '页面设置...',
            click: () => {
              this.broadcastToRenderer('menu-page-setup');
            }
          },
          {
            label: '打印...',
            accelerator: 'CmdOrCtrl+P',
            click: () => {
              this.broadcastToRenderer('menu-print');
            }
          }
        ]
      },
      {
        label: '编辑',
        submenu: [
          { role: 'undo', label: '撤销' },
          { role: 'redo', label: '重做' },
          { type: 'separator' },
          { role: 'cut', label: '剪切' },
          { role: 'copy', label: '复制' },
          { role: 'paste', label: '粘贴' },
          { role: 'selectall', label: '全选' },
          { type: 'separator' },
          {
            label: '查找',
            accelerator: 'CmdOrCtrl+F',
            click: () => {
              this.broadcastToRenderer('menu-find');
            }
          },
          {
            label: '查找下一个',
            accelerator: 'F3',
            click: () => {
              this.broadcastToRenderer('menu-find-next');
            }
          },
          {
            label: '替换',
            accelerator: 'CmdOrCtrl+H',
            click: () => {
              this.broadcastToRenderer('menu-replace');
            }
          }
        ]
      },
      {
        label: '视图',
        submenu: [
          {
            label: '重新加载',
            accelerator: 'CmdOrCtrl+R',
            click: () => {
              this.windowManager.reload('main');
            }
          },
          {
            label: '强制重新加载',
            accelerator: 'CmdOrCtrl+Shift+R',
            click: () => {
              this.windowManager.forceReload('main');
            }
          },
          {
            label: '切换开发者工具',
            accelerator: process.platform === 'darwin' ? 'Alt+Cmd+I' : 'Ctrl+Shift+I',
            click: () => {
              this.windowManager.openDevTools('main');
            }
          },
          { type: 'separator' },
          {
            label: '实际大小',
            accelerator: 'CmdOrCtrl+0',
            click: () => {
              this.broadcastToRenderer('menu-zoom-reset');
            }
          },
          {
            label: '放大',
            accelerator: 'CmdOrCtrl+Plus',
            click: () => {
              this.broadcastToRenderer('menu-zoom-in');
            }
          },
          {
            label: '缩小',
            accelerator: 'CmdOrCtrl+-',
            click: () => {
              this.broadcastToRenderer('menu-zoom-out');
            }
          },
          { type: 'separator' },
          {
            label: '切换全屏',
            accelerator: process.platform === 'darwin' ? 'Ctrl+Cmd+F' : 'F11',
            click: () => {
              const mainWindow = this.windowManager.getWindow('main');
              if (mainWindow) {
                mainWindow.setFullScreen(!mainWindow.isFullScreen());
              }
            }
          },
          { type: 'separator' },
          {
            label: '总是在前台',
            type: 'checkbox',
            checked: false,
            click: (item) => {
              const mainWindow = this.windowManager.getWindow('main');
              if (mainWindow) {
                mainWindow.setAlwaysOnTop(item.checked);
              }
            }
          },
          {
            label: '隐藏窗口边框',
            type: 'checkbox',
            checked: false,
            click: (item) => {
              const mainWindow = this.windowManager.getWindow('main');
              if (mainWindow) {
                mainWindow.setFrame(item.checked);
              }
            }
          }
        ]
      },
      {
        label: '窗口',
        submenu: [
          {
            label: '最小化',
            accelerator: 'CmdOrCtrl+M',
            role: 'minimize'
          },
          {
            label: '关闭',
            accelerator: 'CmdOrCtrl+W',
            role: 'close'
          },
          ...(process.platform === 'darwin' ? [
            { type: 'separator' },
            { role: 'front', label: '置于最前' },
            { type: 'separator' },
            {
              label: '显示所有',
              role: 'arrangeInFront'
            }
          ] : []),
          { type: 'separator' },
          {
            label: '新窗口',
            accelerator: 'CmdOrCtrl+Shift+N',
            click: () => {
              this.createNewWindow();
            }
          },
          {
            label: '显示/隐藏侧边栏',
            accelerator: 'CmdOrCtrl+\\',
            click: () => {
              this.broadcastToRenderer('menu-toggle-sidebar');
            }
          }
        ]
      },
      {
        label: '帮助',
        submenu: [
          {
            label: 'Py Copilot 帮助',
            accelerator: 'F1',
            click: () => {
              this.openHelp();
            }
          },
          { type: 'separator' },
          {
            label: '键盘快捷键',
            click: () => {
              this.showShortcuts();
            }
          },
          {
            label: '许可证信息',
            click: () => {
              this.showLicense();
            }
          },
          { type: 'separator' },
          {
            label: '检查更新...',
            click: () => {
              this.broadcastToRenderer('menu-check-updates');
            }
          },
          { type: 'separator' },
          {
            label: '关于',
            click: () => {
              this.showAbout();
            }
          }
        ]
      }
    ];
  }

  /**
   * 设置菜单
   */
  setMenu(template) {
    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
  }

  /**
   * 获取当前菜单
   */
  getMenu() {
    return Menu.getApplicationMenu();
  }

  /**
   * 更新菜单项
   */
  updateMenuItem(label, newItem) {
    const menu = this.getMenu();
    if (!menu) return;

    // 查找并更新菜单项
    menu.items.forEach((item) => {
      if (item.label === label) {
        Object.assign(item, newItem);
      }
      if (item.submenu) {
        this.updateSubmenuItem(item.submenu, label, newItem);
      }
    });

    this.setMenu(menu.items);
  }

  /**
   * 更新子菜单项
   */
  updateSubmenuItem(submenu, label, newItem) {
    submenu.items.forEach((item) => {
      if (item.label === label) {
        Object.assign(item, newItem);
      }
      if (item.submenu) {
        this.updateSubmenuItem(item.submenu, label, newItem);
      }
    });
  }

  /**
   * 启用/禁用菜单项
   */
  setMenuItemEnabled(label, enabled) {
    const menu = this.getMenu();
    if (!menu) return;

    menu.items.forEach((item) => {
      if (item.label === label) {
        item.enabled = enabled;
      }
      if (item.submenu) {
        this.setSubmenuItemEnabled(item.submenu, label, enabled);
      }
    });

    this.setMenu(menu.items);
  }

  /**
   * 设置子菜单项启用状态
   */
  setSubmenuItemEnabled(submenu, label, enabled) {
    submenu.items.forEach((item) => {
      if (item.label === label) {
        item.enabled = enabled;
      }
      if (item.submenu) {
        this.setSubmenuItemEnabled(item.submenu, label, enabled);
      }
    });
  }

  /**
   * 添加菜单项
   */
  addMenuItem(parentLabel, newItem) {
    const menu = this.getMenu();
    if (!menu) return;

    const parent = this.findMenuItem(menu.items, parentLabel);
    if (parent && parent.submenu) {
      parent.submenu.append(new MenuItem(newItem));
      this.setMenu(menu.items);
    }
  }

  /**
   * 查找菜单项
   */
  findMenuItem(items, label) {
    for (const item of items) {
      if (item.label === label) {
        return item;
      }
      if (item.submenu) {
        const found = this.findMenuItem(item.submenu.items, label);
        if (found) return found;
      }
    }
    return null;
  }

  /**
   * 广播消息到渲染进程
   */
  broadcastToRenderer(channel, data = null) {
    this.windowManager.broadcast(channel, data);
  }

  /**
   * 处理文件打开
   */
  async handleOpenFile() {
    const result = await dialog.showOpenDialog(this.windowManager.getWindow('main'), {
      properties: ['openFile'],
      filters: [
        { name: '支持的文件', extensions: ['json', 'txt', 'md', 'csv', 'pdf'] },
        { name: 'JSON', extensions: ['json'] },
        { name: '文本文件', extensions: ['txt', 'md'] },
        { name: 'CSV文件', extensions: ['csv'] },
        { name: 'PDF文件', extensions: ['pdf'] },
        { name: '所有文件', extensions: ['*'] }
      ]
    });

    if (!result.canceled && result.filePaths.length > 0) {
      this.broadcastToRenderer('menu-open-file', result.filePaths[0]);
    }
  }

  /**
   * 显示首选项
   */
  showPreferences() {
    this.windowManager.createModalWindow({
      width: 600,
      height: 500,
      title: '首选项',
      resizable: false,
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <title>首选项</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; }
            .section { margin-bottom: 30px; }
            .section h3 { margin-bottom: 10px; color: #333; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: 500; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            .checkbox { display: flex; align-items: center; }
            .checkbox input { width: auto; margin-right: 8px; }
            button { padding: 10px 20px; background: #007AFF; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056CC; }
          </style>
        </head>
        <body>
          <h2>应用首选项</h2>
          
          <div class="section">
            <h3>常规设置</h3>
            <div class="form-group">
              <label>默认语言</label>
              <select>
                <option value="zh-CN">简体中文</option>
                <option value="en-US">English</option>
              </select>
            </div>
            <div class="form-group checkbox">
              <input type="checkbox" id="autoSave" checked>
              <label for="autoSave">自动保存</label>
            </div>
          </div>
          
          <div class="section">
            <h3>外观</h3>
            <div class="form-group checkbox">
              <input type="checkbox" id="darkMode">
              <label for="darkMode">深色模式</label>
            </div>
            <div class="form-group checkbox">
              <input type="checkbox" id="showAnimations" checked>
              <label for="showAnimations">显示动画</label>
            </div>
          </div>
          
          <div class="section">
            <h3>通知</h3>
            <div class="form-group checkbox">
              <input type="checkbox" id="desktopNotifications" checked>
              <label for="desktopNotifications">桌面通知</label>
            </div>
            <div class="form-group checkbox">
              <input type="checkbox" id="soundNotifications">
              <label for="soundNotifications">声音通知</label>
            </div>
          </div>
          
          <div class="section">
            <button onclick="savePreferences()">保存</button>
            <button onclick="window.close()" style="background: #ccc; margin-left: 10px;">取消</button>
          </div>
          
          <script>
            function savePreferences() {
              const preferences = {
                language: document.querySelector('select').value,
                autoSave: document.getElementById('autoSave').checked,
                darkMode: document.getElementById('darkMode').checked,
                showAnimations: document.getElementById('showAnimations').checked,
                desktopNotifications: document.getElementById('desktopNotifications').checked,
                soundNotifications: document.getElementById('soundNotifications').checked
              };
              
              window.electronAPI.savePreferences(preferences);
              window.close();
            }
          </script>
        </body>
        </html>
      `
    });
  }

  /**
   * 创建新窗口
   */
  createNewWindow() {
    this.windowManager.createMainWindow();
  }

  /**
   * 打开帮助
   */
  openHelp() {
    const { shell } = require('electron');
    shell.openExternal('https://pycopilot.com/help');
  }

  /**
   * 显示快捷键
   */
  showShortcuts() {
    this.broadcastToRenderer('menu-show-shortcuts');
  }

  /**
   * 显示许可证
   */
  showLicense() {
    dialog.showMessageBox(this.windowManager.getWindow('main'), {
      type: 'info',
      title: '许可证信息',
      message: 'MIT License',
      detail: 'Copyright (c) 2025 Py Copilot Team\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software...',
      buttons: ['确定']
    });
  }

  /**
   * 显示关于
   */
  showAbout() {
    dialog.showMessageBox(this.windowManager.getWindow('main'), {
      type: 'info',
      title: '关于 Py Copilot',
      message: 'Py Copilot Desktop',
      detail: `版本: ${app.getVersion()}\n\n一个功能强大的AI助手桌面应用程序。\n\n© 2025 Py Copilot Team\n\n更多信息请访问: https://pycopilot.com`,
      buttons: ['确定']
    });
  }

  /**
   * 创建上下文菜单
   */
  createContextMenu(options = {}) {
    const { Menu, MenuItem } = require('electron');
    const contextMenu = new Menu();

    // 基本菜单项
    contextMenu.append(new MenuItem({ role: 'cut', label: '剪切' }));
    contextMenu.append(new MenuItem({ role: 'copy', label: '复制' }));
    contextMenu.append(new MenuItem({ role: 'paste', label: '粘贴' }));
    
    if (options.showDelete) {
      contextMenu.append(new MenuItem({ type: 'separator' }));
      contextMenu.append(new MenuItem({ role: 'delete', label: '删除' }));
    }

    if (options.customItems) {
      contextMenu.append(new MenuItem({ type: 'separator' }));
      options.customItems.forEach(item => {
        contextMenu.append(new MenuItem(item));
      });
    }

    return contextMenu;
  }

  /**
   * 显示上下文菜单
   */
  showContextMenu(x, y, options = {}) {
    const contextMenu = this.createContextMenu(options);
    contextMenu.popup(options.browserWindow || this.windowManager.getWindow('main'));
  }

  /**
   * 添加自定义菜单项
   */
  addCustomMenuItem(menuPath, item) {
    const menu = this.getMenu();
    if (!menu) return;

    const path = menuPath.split('.');
    let current = menu.items;

    for (let i = 0; i < path.length - 1; i++) {
      const menuItem = this.findMenuItem(current, path[i]);
      if (menuItem && menuItem.submenu) {
        current = menuItem.submenu.items;
      } else {
        console.warn(`菜单路径 ${menuPath} 不存在`);
        return;
      }
    }

    const parentItem = this.findMenuItem(current, path[path.length - 1]);
    if (parentItem && parentItem.submenu) {
      parentItem.submenu.append(new MenuItem(item));
      this.setMenu(menu.items);
    }
  }
}

module.exports = MenuManager;