// 支持Cypress测试的全局文件和命令
import './commands'; // 导入自定义命令

// 自定义命令
Cypress.Commands.add('login', (username, password) => {
  cy.session([username, password], () => {
    cy.visit('/login');
    cy.get('[data-testid="username-input"]').type(username);
    cy.get('[data-testid="password-input"]').type(password);
    cy.get('[data-testid="login-button"]').click();
    
    // 等待页面重定向
    cy.url().should('not.include', '/login');
  });
});

// 重置数据库（需要后端API支持）
Cypress.Commands.add('resetDatabase', () => {
  // 调用后端API重置测试数据
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/test/reset-db`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('access_token')}`
    },
    body: {
      resetTables: ['models', 'suppliers', 'default_models', 'users']
    }
  });
});

// 添加一些调试命令
Cypress.Commands.add('consoleLog', (message) => {
  cy.log(message);
  console.log(message);
});

// 在测试前设置全局状态
beforeEach(() => {
  // 清除所有存储
  cy.clearLocalStorage();
  cy.clearCookies();
  
  // 如果需要登录，执行登录
  // cy.login('admin', 'admin123');
});

// 在所有测试后执行清理
afterEach(() => {
  // 清理任何可能影响其他测试的状态
});

// 忽略特定的网络请求错误
Cypress.on('uncaught:exception', (err, runnable) => {
  // 忽略特定错误
  if (err.message.includes('ResizeObserver loop limit exceeded') ||
      err.message.includes('Script error') ||
      err.message.includes('Non-Error promise rejection captured')) {
    return false;
  }
  
  // 让其他错误通过，使测试失败
  return true;
});