# Py Copilot Desktop Application

这是 Py Copilot 的桌面应用程序版本，基于 Electron 构建，提供完整的桌面体验。

## 特性

- 🚀 跨平台支持 (Windows, macOS, Linux)
- 🎨 现代化UI界面
- 🔧 原生系统集成
- 📁 文件系统访问
- 🔔 系统通知
- ⌨️ 快捷键支持
- 📊 系统监控
- 🔄 自动更新支持

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm 或 yarn
- Electron >= 28.0.0

### 安装依赖

```bash
cd electron
npm install
```

### 开发模式

```bash
# 启动开发环境
npm run dev
```

### 构建应用

```bash
# 构建所有平台
npm run build

# 构建特定平台
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

### 打包应用

```bash
# 打包为分发包
npm run dist

# 打包所有平台
npm run dist-all
```

## 项目结构

```
electron/
├── main.js                 # 主进程文件
├── preload.js             # 预加载脚本
├── package.json           # Electron包配置
├── icons/                 # 应用图标
│   ├── icon.svg          # SVG图标源文件
│   ├── icon.ico          # Windows图标
│   └── icon.icns         # macOS图标
├── entitlements.mac.plist # macOS权限配置
├── installer.nsh          # Windows安装脚本
└── src/                   # 源代码目录
    ├── window-manager.js  # 窗口管理
    ├── menu-manager.js    # 菜单管理
    ├── system-tray.js     # 系统托盘
    └── updater.js         # 自动更新
```

## API 接口

### 文件操作

```javascript
// 打开文件
const result = await window.electronAPI.openFile();
if (!result.canceled) {
}

// 保存文件
await window.electronAPI.saveFile('document.json', JSON.stringify(data));
```

### 系统信息

```javascript
// 获取系统信息
const systemInfo = await window.electronAPI.getSystemInfo();
console.log('系统平台:', systemInfo.platform);

// 获取应用版本
const version = await window.electronAPI.getAppVersion();
console.log('应用版本:', version);
```

### 窗口控制

```javascript
// 窗口操作
await window.electronAPI.minimizeWindow();  // 最小化
await window.electronAPI.maximizeWindow();  // 最大化/还原
await window.electronAPI.closeWindow();     // 关闭
```

### 剪贴板

```javascript
// 写入剪贴板
await window.electronAPI.writeClipboardText('Hello World');

// 读取剪贴板
const text = await window.electronAPI.readClipboardText();
```

### 通知

```javascript
// 显示通知
await window.electronAPI.showNotification({
  title: '任务完成',
  body: '您的文件已成功保存'
});
```

### 菜单事件监听

```javascript
// 监听菜单事件
window.electronAPI.onMenuAction((event, data) => {
  switch (event) {
    case 'menu-new':
      console.log('新建文件');
      break;
    case 'menu-open-file':
      console.log('打开文件:', data);
      break;
    case 'menu-save':
      console.log('保存文件');
      break;
  }
});
```

## 开发指南

### 主进程 (main.js)

主进程负责：
- 创建和管理应用窗口
- 处理系统事件
- 与操作系统交互
- 管理文件系统和剪贴板

### 渲染进程 (preload.js)

预加载脚本提供安全的API接口给渲染进程，实现：
- 上下文隔离
- API暴露
- 安全验证

### 前端集成

在React组件中集成Electron API：

```javascript
import React, { useEffect } from 'react';

const FileManager = () => {
  const handleOpenFile = async () => {
    try {
      const result = await window.electronAPI.openFile();
      if (!result.canceled) {
        // 处理文件
        console.log('文件路径:', result.filePaths[0]);
      }
    } catch (error) {
      console.error('打开文件失败:', error);
    }
  };

  return (
    <button onClick={handleOpenFile}>
      打开文件
    </button>
  );
};
```

### 安全考虑

1. **上下文隔离**: 使用 `contextIsolation: true`
2. **禁用Node集成**: `nodeIntegration: false`
3. **预加载脚本**: 限制API访问范围
4. **CSP策略**: 配置内容安全策略
5. **权限控制**: 仅暴露必要功能

### 调试

```bash
# 启动开发模式（自动打开开发者工具）
npm run dev

# 手动打开开发者工具
window.devAPI.openDevTools();
```

## 构建配置

### Windows

- 生成 NSIS 安装包
- 生成便携版
- 支持 x64 架构

### macOS

- 生成 DMG 镜像
- 生成 ZIP 压缩包
- 支持 Intel 和 Apple Silicon
- 代码签名和公证

### Linux

- 生成 AppImage
- 生成 DEB 包
- 生成 RPM 包
- 支持 x64 架构

## 部署

### 自动更新

应用支持通过 electron-updater 实现自动更新：

```javascript
// 检查更新
await window.electronAPI.checkForUpdates();

// 监听更新事件
ipcMain.on('update-available', () => {
  // 显示更新通知
});
```

### 代码签名

在生产环境中，需要配置代码签名：

1. Windows: 使用代码签名证书
2. macOS: 使用 Apple Developer ID
3. Linux: 可选，使用 GPG 签名

## 故障排除

### 常见问题

1. **应用无法启动**
   - 检查 Electron 版本兼容性
   - 验证文件路径是否正确

2. **API 调用失败**
   - 确认上下文隔离设置
   - 检查预加载脚本加载

3. **构建失败**
   - 清理 node_modules 和缓存
   - 检查依赖版本兼容性

4. **权限错误**
   - 验证 macOS 权限配置
   - 检查 Windows UAC 设置

### 日志

开发模式下可以在控制台查看详细日志：

```javascript
// 启用详细日志
console.log('Main process:', process.versions);
console.log('Electron API:', window.electronAPI);
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License - 详见 LICENSE 文件

## 支持

如有问题或建议，请通过以下方式联系：

- GitHub Issues: https://github.com/pycopilot/desktop/issues
- 邮箱: team@pycopilot.com
- 官网: https://pycopilot.com

## 更新日志

### v1.0.0 (2025-01-05)

- 🎉 首次发布
- ✨ 基础桌面应用功能
- 🔧 文件系统集成
- 🎨 现代化UI界面
- 🔔 系统通知支持
- ⌨️ 快捷键支持
- 📊 跨平台兼容性