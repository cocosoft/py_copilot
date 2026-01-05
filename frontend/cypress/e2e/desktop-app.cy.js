// 桌面应用的端到端测试
describe('桌面应用功能', () => {
  // 测试前的准备工作
  before(() => {
    // 启动桌面应用
    cy.visit('http://localhost:4000');
    
    // 重置本地数据库
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/test/setup`,
      headers: {
        'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
      },
      body: {
        setupType: 'desktop_app'
      }
    });
  });

  // 测试桌面应用启动
  it('桌面应用应该能够正常启动', () => {
    // 验证应用窗口出现
    cy.get('[data-testid="desktop-window"]').should('be.visible');
    
    // 验证标题栏
    cy.get('[data-testid="app-title"]').should('contain', 'Py Copilot');
    
    // 验证导航菜单
    cy.get('[data-testid="navigation-menu"]').should('be.visible');
    
    // 验证默认模型管理菜单项
    cy.get('[data-testid="nav-item-default-models"]').should('be.visible');
  });

  // 测试离线模式
  it('桌面应用应该支持离线模式', () => {
    // 断开网络连接
    cy.visit('http://localhost:4000', {
      onBeforeLoad(win) {
        // 模拟离线状态
        cy.stub(win.navigator, 'onLine').get(() => false);
      }
    });
    
    // 验证应用在离线模式下仍可使用
    cy.get('[data-testid="offline-indicator"]').should('be.visible');
    cy.get('[data-testid="offline-message"]').should('contain', '当前处于离线模式');
    
    // 验证离线状态下的基本功能
    cy.get('[data-testid="nav-item-default-models"]').click();
    cy.get('[data-testid="default-models-page"]').should('be.visible');
    
    // 验证离线模式下的数据加载（使用本地缓存）
    cy.get('[data-testid="default-models-list"]').should('be.visible');
    
    // 重新连接网络
    cy.visit('http://localhost:4000', {
      onBeforeLoad(win) {
        // 模拟在线状态
        cy.stub(win.navigator, 'onLine').get(() => true);
      }
    });
    
    // 验证应用状态恢复到在线
    cy.get('[data-testid="offline-indicator"]').should('not.exist');
  });

  // 测试本地存储
  it('桌面应用应该正确处理本地存储', () => {
    // 访问默认模型管理页面
    cy.get('[data-testid="nav-item-default-models"]').click();
    
    // 修改一个设置
    cy.get('[data-testid="model-selector"]').click();
    cy.get('[data-testid="model-option-GPT-4"]').click();
    cy.get('[data-testid="save-settings"]').click();
    
    // 关闭应用
    cy.get('[data-testid="close-app-button"]').click();
    
    // 重新启动应用
    cy.visit('http://localhost:4000');
    
    // 验证设置已保存
    cy.get('[data-testid="nav-item-default-models"]').click();
    cy.get('[data-testid="model-selector"]').should('contain', 'GPT-4');
  });

  // 测试本地数据库同步
  it('桌面应用应该能够与后端同步数据', () => {
    // 启动应用
    cy.visit('http://localhost:4000');
    
    // 手动触发同步
    cy.get('[data-testid="sync-button"]').click();
    
    // 验证同步状态
    cy.get('[data-testid="sync-status"]').should('contain', '正在同步...');
    
    // 等待同步完成
    cy.get('[data-testid="sync-status"]', { timeout: 10000 }).should('contain', '同步完成');
  });

  // 测试自动更新检查
  it('桌面应用应该能够检查和显示更新', () => {
    // 模拟有可用的更新
    cy.intercept('GET', `${Cypress.env('apiUrl')}/updates/check`, {
      statusCode: 200,
      body: {
        hasUpdate: true,
        version: '1.2.3',
        downloadUrl: 'https://example.com/update/download',
        releaseNotes: '新功能和错误修复'
      }
    }).as('checkUpdate');
    
    // 访问设置页面
    cy.get('[data-testid="nav-item-settings"]').click();
    cy.get('[data-testid="about-tab"]').click();
    
    // 点击检查更新按钮
    cy.get('[data-testid="check-update-button"]').click();
    
    // 等待更新检查请求
    cy.wait('@checkUpdate');
    
    // 验证显示更新通知
    cy.get('[data-testid="update-notification"]').should('be.visible');
    cy.get('[data-testid="update-notification"]').should('contain', '有可用更新');
    
    // 验证显示更新详情
    cy.get('[data-testid="update-version"]').should('contain', '1.2.3');
    cy.get('[data-testid="update-release-notes"]').should('contain', '新功能和错误修复');
  });

  // 测试窗口大小调整
  it('桌面应用应该能够调整窗口大小', () => {
    // 访问默认模型管理页面
    cy.get('[data-testid="nav-item-default-models"]').click();
    
    // 调整窗口大小
    cy.window().then((win) => {
      // 设置窗口尺寸
      cy.viewport(1024, 768);
    });
    
    // 验证界面响应式布局
    cy.get('[data-testid="default-models-page"]').should('be.visible');
    cy.get('[data-testid="responsive-layout"]').should('be.visible');
    
    // 再次调整窗口大小
    cy.window().then((win) => {
      cy.viewport(800, 600);
    });
    
    // 验证移动端布局
    cy.get('[data-testid="mobile-menu-button"]').should('be.visible');
    cy.get('[data-testid="mobile-menu"]').click();
  });

  // 测试快捷键
  it('桌面应用应该支持快捷键操作', () => {
    // 访问默认模型管理页面
    cy.get('[data-testid="nav-item-default-models"]').click();
    
    // 使用快捷键打开模型选择器
    cy.get('body').type('{ctrl+m}');
    
    // 验证模型选择器打开
    cy.get('[data-testid="model-selector-modal"]').should('be.visible');
    
    // 使用快捷键关闭模型选择器
    cy.get('body').type('{esc}');
    
    // 验证模型选择器关闭
    cy.get('[data-testid="model-selector-modal"]').should('not.exist');
  });

  // 测试菜单功能
  it('桌面应用应该正确处理菜单操作', () => {
    // 打开文件菜单
    cy.get('[data-testid="menu-file"]').click();
    
    // 验证文件菜单项
    cy.get('[data-testid="menu-item-new-model"]').should('be.visible');
    cy.get('[data-testid="menu-item-export-settings"]').should('be.visible');
    cy.get('[data-testid="menu-item-import-settings"]').should('be.visible');
    
    // 点击导入设置
    cy.get('[data-testid="menu-item-import-settings"]').click();
    
    // 验证文件选择对话框出现
    cy.get('[data-testid="file-dialog"]').should('be.visible');
    
    // 取消对话框
    cy.get('[data-testid="file-dialog-cancel"]').click();
    
    // 验证对话框关闭
    cy.get('[data-testid="file-dialog"]').should('not.exist');
  });

  // 测试通知系统
  it('桌面应用应该正确显示通知', () => {
    // 模拟发送通知
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/notifications/send`,
      headers: {
        'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
      },
      body: {
        title: '默认模型已更新',
        message: '全局默认模型已成功更新为 GPT-4',
        type: 'success'
      }
    });
    
    // 等待通知出现
    cy.get('[data-testid="notification"]', { timeout: 5000 }).should('be.visible');
    
    // 验证通知内容
    cy.get('[data-testid="notification-title"]').should('contain', '默认模型已更新');
    cy.get('[data-testid="notification-message"]').should('contain', '全局默认模型已成功更新为 GPT-4');
    cy.get('[data-testid="notification-icon-success"]').should('be.visible');
  });

  // 测试错误处理
  it('桌面应用应该正确处理错误', () => {
    // 模拟API错误
    cy.intercept('GET', `${Cypress.env('apiUrl')}/default-models`, {
      statusCode: 500,
      body: {
        detail: '服务器内部错误'
      }
    });
    
    // 访问默认模型管理页面
    cy.get('[data-testid="nav-item-default-models"]').click();
    
    // 验证显示错误消息
    cy.get('[data-testid="error-message"]').should('be.visible');
    cy.get('[data-testid="error-message"]').should('contain', '服务器内部错误');
    
    // 验证显示重试按钮
    cy.get('[data-testid="retry-button"]').should('be.visible');
    
    // 点击重试按钮
    cy.get('[data-testid="retry-button"]').click();
    
    // 等待重试
    cy.get('[data-testid="loading-indicator"]').should('be.visible');
  });

  // 测试性能
  it('桌面应用应该具有可接受的性能', () => {
    // 记录页面加载时间
    const startTime = Date.now();
    
    // 访问默认模型管理页面
    cy.get('[data-testid="nav-item-default-models"]').click();
    
    // 等待页面完全加载
    cy.get('[data-testid="default-models-page"]').should('be.visible');
    
    // 计算加载时间
    cy.window().then((win) => {
      const loadTime = Date.now() - startTime;
      
      // 验证加载时间小于2秒
      expect(loadTime).to.be.lessThan(2000);
      
      // 记录加载时间到控制台
      cy.log(`页面加载时间: ${loadTime}ms`);
    });
  });
});