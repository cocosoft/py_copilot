// Cypress自定义命令
// 这些命令会在每个测试文件中自动加载

// 为Cypress添加类型声明
/// <reference types="cypress" />

// 获取默认模型列表
Cypress.Commands.add('getDefaultModels', () => {
  return cy.request({
    method: 'GET',
    url: `${Cypress.env('apiUrl')}/default-models`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
    }
  });
});

// 创建全局默认模型
Cypress.Commands.add('createGlobalDefaultModel', (modelId, priority = 1, fallbackModelId = null) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/default-models/global`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
    },
    body: {
      model_id: modelId,
      priority,
      fallback_model_id: fallbackModelId
    }
  });
});

// 创建场景默认模型
Cypress.Commands.add('createSceneDefaultModel', (scene, modelId, priority = 1, fallbackModelId = null) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/default-models/scene`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
    },
    body: {
      scene,
      model_id: modelId,
      priority,
      fallback_model_id: fallbackModelId
    }
  });
});

// 等待API请求完成
Cypress.Commands.add('waitForApi', (alias) => {
  cy.wait(alias);
  return cy.get(alias).its('response.statusCode').should('be.oneOf', [200, 201]);
});

// 模拟用户选择模型
Cypress.Commands.add('selectModel', (modelName) => {
  cy.get('[data-testid="model-selector"]').click();
  cy.get('[data-testid="model-search-input"]').type(modelName);
  cy.get(`[data-testid="model-option-${modelName}"]`).click();
  cy.get('[data-testid="model-selector"]').contains(modelName);
});

// 检查模型选择器是否显示正确模型
Cypress.Commands.add('shouldDisplayModel', (modelName) => {
  cy.get('[data-testid="model-selector"]').should('contain', modelName);
});

// 检查是否显示默认模型
Cypress.Commands.add('shouldDisplayDefaultModel', (modelName) => {
  cy.get('[data-testid="default-model-indicator"]').should('contain', modelName);
});

// 检查模型参数配置是否正确
Cypress.Commands.add('checkModelParameters', (modelName, params) => {
  // 打开参数配置面板
  cy.get('[data-testid="parameter-config-button"]').click();
  
  // 验证参数
  Object.keys(params).forEach(paramName => {
    cy.get(`[data-testid="parameter-input-${paramName}"]`).should('have.value', params[paramName]);
  });
  
  // 关闭参数配置面板
  cy.get('[data-testid="parameter-config-close"]').click();
});

// 检查API响应数据
Cypress.Commands.add('checkApiResponse', (statusCode = 200) => {
  cy.get('@apiResponse').its('status').should('eq', statusCode);
});

// 设置API响应别名
Cypress.Commands.add('setApiAlias', (method, url) => {
  cy.intercept(method, url).as('apiCall');
  return cy.get('@apiCall');
});

// 验证用户权限
Cypress.Commands.add('checkUserPermission', (requiredPermission) => {
  cy.request({
    method: 'GET',
    url: `${Cypress.env('apiUrl')}/users/me`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
    }
  }).then(response => {
    const user = response.body;
    if (user.is_superuser) {
      // 超级用户拥有所有权限
      return true;
    }
    
    // 检查特定权限
    return cy.request({
      method: 'GET',
      url: `${Cypress.env('apiUrl')}/permissions/${requiredPermission}`,
      headers: {
        'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
      }
    }).then(permissionResponse => {
      const hasPermission = permissionResponse.body && permissionResponse.body.has_permission;
      expect(hasPermission).to.be.true;
    });
  });
});

// 模拟桌面应用中的导航
Cypress.Commands.add('navigateInDesktopApp', (path) => {
  // 模拟桌面应用中的导航
  cy.get('[data-testid="desktop-nav"]').click();
  cy.get(`[data-testid="nav-item-${path}"]`).click();
  cy.url().should('include', path);
});