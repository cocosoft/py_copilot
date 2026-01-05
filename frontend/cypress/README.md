# 端到端测试指南

## 概述

本指南介绍了如何使用Cypress运行默认模型管理功能的端到端测试。

## 环境准备

1. 安装依赖

```bash
cd frontend
npm install
```

2. 启动开发服务器

```bash
# 启动前端开发服务器
npm run dev

# 在另一个终端，启动后端API服务器
cd ../backend
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

3. 启动桌面应用（可选）

```bash
# 如果要测试桌面应用功能
cd ../electron
npm run start
```

## 运行测试

### 使用Cypress测试运行器

1. 打开Cypress测试运行器

```bash
cd frontend
npm run cypress:open
```

2. 在Cypress界面中：
   - 选择浏览器（Chrome、Firefox或Edge）
   - 点击测试套件运行

### 使用命令行运行测试

1. 运行所有测试

```bash
cd frontend
npm run cypress:run
```

2. 运行特定测试套件

```bash
# 运行默认模型管理测试
npm run cypress:run -- --spec "cypress/e2e/default-model-management.cy.js"

# 运行桌面应用测试
npm run cypress:run -- --spec "cypress/e2e/desktop-app.cy.js"
```

3. 在特定浏览器中运行

```bash
# 在Chrome中运行
npm run cypress:run:chrome

# 在Firefox中运行
npm run cypress:run:firefox

# 在Edge中运行
npm run cypress:run:edge
```

4. 无头模式运行（用于CI/CD）

```bash
npm run cypress:run:headless
```

## 测试报告

测试运行完成后，Cypress会生成以下报告：

- 测试视频：`cypress/videos/`
- 测试截图：`cypress/screenshots/`
- 控制台日志：显示在终端中

## 测试覆盖场景

### 默认模型管理测试

- 超级用户设置全局默认模型
- 超级用户设置场景默认模型
- 普通用户查看默认模型（权限控制）
- 模型选择器显示默认模型
- 模型回退机制
- 默认模型的优先级排序
- 全局默认模型删除
- 权限控制
- API集成
- 错误处理

### 桌面应用测试

- 桌面应用启动
- 离线模式
- 本地存储
- 本地数据库同步
- 自动更新检查
- 窗口大小调整
- 快捷键操作
- 菜单功能
- 通知系统
- 错误处理
- 性能测试

## 故障排除

### 常见问题

1. **无法连接到开发服务器**
   - 确保前端和后端服务器都在运行
   - 检查端口是否冲突

2. **测试超时**
   - 增加测试超时时间
   - 检查网络连接

3. **认证失败**
   - 确保测试用户已创建
   - 检查令牌有效性

### 调试技巧

1. **使用调试命令**

```javascript
// 在测试中添加调试输出
cy.log('调试信息');

// 暂停测试执行
cy.pause();

// 查看浏览器控制台
cy.get('body').invoke('text').then(console.log);
```

2. **查看测试视频**

- 测试视频保存在 `cypress/videos/` 目录
- 可以播放视频查看测试执行过程

3. **使用开发者工具**

- 在测试中添加 `cy.debug()` 暂停测试
- 在Cypress测试运行器中打开开发者工具
- 检查网络请求和响应

## 编写新测试

1. 创建新的测试文件

```javascript
// cypress/e2e/new-feature.cy.js
describe('新功能测试', () => {
  beforeEach(() => {
    // 每个测试前的准备工作
  });

  it('应该能够执行新功能', () => {
    // 测试步骤
  });

  afterEach(() => {
    // 每个测试后的清理工作
  });
});
```

2. 使用Cypress命令

```javascript
// 使用已有的命令
cy.login('username', 'password');

// 使用自定义命令
cy.createGlobalDefaultModel(1, 1, 2);
cy.selectModel('GPT-3.5');
cy.shouldDisplayDefaultModel('GPT-3.5');
```

## 参考资源

- [Cypress官方文档](https://docs.cypress.io/)
- [Cypress API参考](https://docs.cypress.io/api/table-of-contents)
- [Cypress测试最佳实践](https://docs.cypress.io/guides/references/best-practices)