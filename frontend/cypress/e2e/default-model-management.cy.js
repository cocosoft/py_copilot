// 默认模型管理的端到端测试
describe('默认模型管理', () => {
  // 测试前的准备工作
  before(() => {
    // 重置数据库，确保测试环境干净
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/test/setup`,
      headers: {
        'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
      },
      body: {
        setupType: 'default_models'
      }
    });
  });

  // 测试超级用户设置全局默认模型
  it('超级用户应该能够设置全局默认模型', () => {
    // 以超级用户身份登录
    cy.login('admin', 'admin123');
    
    // 访问默认模型管理页面
    cy.visit('/default-models');
    
    // 点击"设置全局默认模型"按钮
    cy.get('[data-testid="set-global-default-button"]').click();
    
    // 选择一个模型作为全局默认
    cy.get('[data-testid="model-selector"]').click();
    cy.get('[data-testid="model-search-input"]').type('GPT-3.5');
    cy.get('[data-testid="model-option-GPT-3.5"]').click();
    
    // 设置优先级
    cy.get('[data-testid="priority-input"]').clear().type('1');
    
    // 选择回退模型
    cy.get('[data-testid="fallback-model-selector"]').click();
    cy.get('[data-testid="model-search-input"]').type('GPT-4');
    cy.get('[data-testid="model-option-GPT-4"]').click();
    
    // 点击保存
    cy.get('[data-testid="save-global-default-button"]').click();
    
    // 验证设置成功
    cy.get('[data-testid="success-message"]').should('contain', '全局默认模型设置成功');
    
    // 验证模型选择器显示正确的默认模型
    cy.shouldDisplayDefaultModel('GPT-3.5');
  });

  // 测试超级用户设置场景默认模型
  it('超级用户应该能够设置场景默认模型', () => {
    // 以超级用户身份登录
    cy.login('admin', 'admin123');
    
    // 访问默认模型管理页面
    cy.visit('/default-models');
    
    // 点击"设置场景默认模型"按钮
    cy.get('[data-testid="set-scene-default-button"]').click();
    
    // 选择场景
    cy.get('[data-testid="scene-selector"]').click();
    cy.get('[data-testid="scene-option-chat"]').click();
    
    // 选择模型
    cy.get('[data-testid="model-selector"]').click();
    cy.get('[data-testid="model-search-input"]').type('Claude-3');
    cy.get('[data-testid="model-option-Claude-3"]').click();
    
    // 设置优先级
    cy.get('[data-testid="priority-input"]').clear().type('1');
    
    // 选择回退模型
    cy.get('[data-testid="fallback-model-selector"]').click();
    cy.get('[data-testid="model-search-input"]').type('GPT-3.5');
    cy.get('[data-testid="model-option-GPT-3.5"]').click();
    
    // 点击保存
    cy.get('[data-testid="save-scene-default-button"]').click();
    
    // 验证设置成功
    cy.get('[data-testid="success-message"]').should('contain', '场景默认模型设置成功');
    
    // 验证场景默认模型显示
    cy.get('[data-testid="scene-default-chat"]').should('contain', 'Claude-3');
  });

  // 测试普通用户查看默认模型
  it('普通用户应该能够查看默认模型', () => {
    // 以普通用户身份登录
    cy.login('user', 'user123');
    
    // 访问默认模型管理页面
    cy.visit('/default-models');
    
    // 验证不能编辑默认模型
    cy.get('[data-testid="set-global-default-button"]').should('not.exist');
    cy.get('[data-testid="set-scene-default-button"]').should('not.exist');
    
    // 验证可以看到默认模型列表
    cy.get('[data-testid="default-models-list"]').should('be.visible');
    
    // 验证可以看到全局默认模型
    cy.get('[data-testid="global-default-row"]').should('be.visible');
    
    // 验证可以看到场景默认模型
    cy.get('[data-testid="scene-default-row"]').should('be.visible');
  });

  // 测试模型选择器中的默认模型显示
  it('模型选择器应该显示默认模型', () => {
    // 以任何用户身份登录
    cy.login('user', 'user123');
    
    // 导航到模型选择器页面
    cy.visit('/model-selector');
    
    // 验证默认模型在选择器中显示为默认
    cy.get('[data-testid="model-selector"]').click();
    
    // 检查全局默认模型
    cy.get('[data-testid="model-option-GPT-3.5"]').find('[data-testid="default-badge"]').should('exist');
    
    // 检查场景默认模型
    cy.get('[data-testid="model-option-Claude-3"]').find('[data-testid="scene-default-badge-chat"]').should('exist');
  });

  // 测试模型回退机制
  it('模型不可用时应该自动回退到备选模型', () => {
    // 以任何用户身份登录
    cy.login('user', 'user123');
    
    // 模拟GPT-3.5模型不可用
    cy.intercept('POST', `${Cypress.env('apiUrl')}/chat/completions`, {
      statusCode: 503,
      body: {
        error: {
          message: '模型不可用',
          code: 'MODEL_UNAVAILABLE'
        }
      }
    });
    
    // 选择全局默认模型（GPT-3.5）
    cy.selectModel('GPT-3.5');
    
    // 发送请求
    cy.get('[data-testid="send-button"]').click();
    
    // 等待请求
    cy.get('[data-testid="response-area"]').should('be.visible');
    
    // 验证系统自动回退到备选模型（GPT-4）
    cy.get('[data-testid="model-used-indicator"]').should('contain', 'GPT-4');
    
    // 验证显示回退消息
    cy.get('[data-testid="fallback-message"]').should('contain', '已自动切换到备选模型');
  });

  // 测试默认模型的优先级排序
  it('默认模型应该按优先级排序显示', () => {
    // 以超级用户身份登录
    cy.login('admin', 'admin123');
    
    // 访问默认模型管理页面
    cy.visit('/default-models');
    
    // 验证默认模型列表按优先级排序
    cy.get('[data-testid="default-models-list"]').then(($list) => {
      const priorities = [];
      $list.find('[data-testid="priority-value"]').each((index, element) => {
        priorities.push(parseInt($(element).text()));
      });
      
      // 验证优先级按升序排列
      for (let i = 0; i < priorities.length - 1; i++) {
        expect(priorities[i]).to.be.lessThan(priorities[i + 1]);
      }
    });
  });

  // 测试全局默认模型删除
  it('超级用户应该能够删除全局默认模型', () => {
    // 以超级用户身份登录
    cy.login('admin', 'admin123');
    
    // 访问默认模型管理页面
    cy.visit('/default-models');
    
    // 找到全局默认模型行
    cy.get('[data-testid="global-default-row"]').within(() => {
      // 点击删除按钮
      cy.get('[data-testid="delete-default-model"]').click();
    });
    
    // 确认删除
    cy.get('[data-testid="confirm-delete-button"]').click();
    
    // 验证删除成功
    cy.get('[data-testid="success-message"]').should('contain', '默认模型删除成功');
    
    // 验证全局默认模型不再显示
    cy.get('[data-testid="global-default-row"]').should('not.exist');
  });

  // 测试权限控制
  it('非超级用户应该无法编辑默认模型', () => {
    // 以普通用户身份登录
    cy.login('user', 'user123');
    
    // 访问默认模型管理页面
    cy.visit('/default-models');
    
    // 验证不能编辑全局默认模型
    cy.get('[data-testid="global-default-row"]').within(() => {
      cy.get('[data-testid="edit-default-model"]').should('not.exist');
    });
    
    // 尝试直接访问设置全局默认模型页面
    cy.visit('/default-models/global');
    
    // 应该显示权限不足消息
    cy.get('[data-testid="permission-denied-message"]').should('be.visible');
    cy.get('[data-testid="permission-denied-message"]').should('contain', '权限不足');
  });

  // 测试API集成
  it('前端应该正确处理API响应', () => {
    // 以超级用户身份登录
    cy.login('admin', 'admin123');
    
    // 模拟成功的API响应
    cy.intercept('GET', `${Cypress.env('apiUrl')}/default-models`, {
      statusCode: 200,
      body: {
        total: 2,
        items: [
          {
            id: 1,
            scope: 'global',
            scene: null,
            model_id: 1,
            model_name: 'GPT-3.5',
            priority: 1,
            fallback_model_id: 2,
            fallback_model_name: 'GPT-4',
            is_active: true
          },
          {
            id: 2,
            scope: 'scene',
            scene: 'chat',
            model_id: 3,
            model_name: 'Claude-3',
            priority: 1,
            fallback_model_id: 1,
            fallback_model_name: 'GPT-3.5',
            is_active: true
          }
        ],
        skip: 0,
        limit: 100
      }
    }).as('getDefaultModels');
    
    // 访问默认模型管理页面
    cy.visit('/default-models');
    
    // 等待API调用完成
    cy.wait('@getDefaultModels');
    
    // 验证页面显示正确的默认模型
    cy.get('[data-testid="default-models-list"]').should('be.visible');
    
    // 验证全局默认模型
    cy.get('[data-testid="global-default-row"]').should('contain', 'GPT-3.5');
    cy.get('[data-testid="global-default-row"]').should('contain', 'GPT-4');
    
    // 验证场景默认模型
    cy.get('[data-testid="scene-default-row-chat"]').should('contain', 'Claude-3');
    cy.get('[data-testid="scene-default-row-chat"]').should('contain', 'GPT-3.5');
  });

  // 测试错误处理
  it('前端应该正确处理API错误', () => {
    // 以超级用户身份登录
    cy.login('admin', 'admin123');
    
    // 模拟API错误响应
    cy.intercept('POST', `${Cypress.env('apiUrl')}/default-models/global`, {
      statusCode: 400,
      body: {
        detail: '模型不存在'
      }
    }).as('setGlobalDefaultError');
    
    // 访问默认模型管理页面
    cy.visit('/default-models');
    
    // 点击"设置全局默认模型"按钮
    cy.get('[data-testid="set-global-default-button"]').click();
    
    // 尝试设置一个不存在的模型ID
    cy.window().then((win) => {
      // 手动修改表单值以提交无效数据
      cy.get('[data-testid="model-id-input"]').invoke('val', '9999').trigger('change');
    });
    
    // 点击保存
    cy.get('[data-testid="save-global-default-button"]').click();
    
    // 等待API调用完成
    cy.wait('@setGlobalDefaultError');
    
    // 验证显示错误消息
    cy.get('[data-testid="error-message"]').should('be.visible');
    cy.get('[data-testid="error-message"]').should('contain', '模型不存在');
  });
});