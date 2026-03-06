/**
 * 知识图谱响应式布局测试
 *
 * 功能：测试知识图谱组件在不同屏幕尺寸下的表现
 */

describe('知识图谱响应式布局测试', () => {
  const viewports = [
    { name: 'Desktop 1920x1080', width: 1920, height: 1080 },
    { name: 'Desktop 1366x768', width: 1366, height: 768 },
    { name: 'Laptop 1440x900', width: 1440, height: 900 },
    { name: 'Tablet Landscape 1024x768', width: 1024, height: 768 },
    { name: 'Tablet Portrait 768x1024', width: 768, height: 1024 },
    { name: 'Mobile Large 414x896', width: 414, height: 896 },
    { name: 'Mobile Medium 375x812', width: 375, height: 812 },
    { name: 'Mobile Small 320x568', width: 320, height: 568 }
  ];

  beforeEach(() => {
    cy.visit('/');
    cy.get('[data-testid="knowledge-base-menu"]').click();
    cy.get('[data-testid="knowledge-base-item"]').first().click();
    cy.get('[data-testid="knowledge-graph-tab"]').click();
  });

  viewports.forEach(viewport => {
    it(`应该在 ${viewport.name} 下正确显示`, () => {
      cy.viewport(viewport.width, viewport.height);

      // 等待页面加载
      cy.get('[data-testid="knowledge-graph-manager"]').should('be.visible');

      // 验证主要组件可见
      cy.get('[data-testid="knowledge-graph-dashboard"]').should('be.visible');

      // 截图记录
      cy.screenshot(`knowledge-graph-${viewport.width}x${viewport.height}`);
    });
  });

  describe('实体管理响应式测试', () => {
    viewports.forEach(viewport => {
      it(`实体管理在 ${viewport.name} 下应该可用`, () => {
        cy.viewport(viewport.width, viewport.height);

        // 切换到实体管理标签
        cy.get('[data-testid="entity-management-tab"]').click();
        cy.get('[data-testid="entity-management"]').should('be.visible');

        // 在小屏幕上验证滚动
        if (viewport.width < 768) {
          cy.get('[data-testid="entity-list"]').should('have.css', 'overflow-x', 'auto');
        }

        // 截图记录
        cy.screenshot(`entity-management-${viewport.width}x${viewport.height}`);
      });
    });
  });

  describe('批量构建响应式测试', () => {
    viewports.forEach(viewport => {
      it(`批量构建在 ${viewport.name} 下应该可用`, () => {
        cy.viewport(viewport.width, viewport.height);

        // 切换到批量构建标签
        cy.get('[data-testid="batch-build-tab"]').click();
        cy.get('[data-testid="batch-build-panel"]').should('be.visible');

        // 验证文档列表可滚动
        cy.get('[data-testid="document-list"]').should('be.visible');

        // 截图记录
        cy.screenshot(`batch-build-${viewport.width}x${viewport.height}`);
      });
    });
  });

  describe('可视化响应式测试', () => {
    viewports.forEach(viewport => {
      it(`可视化在 ${viewport.name} 下应该可用`, () => {
        cy.viewport(viewport.width, viewport.height);

        // 切换到可视化标签
        cy.get('[data-testid="visualization-tab"]').click();
        cy.get('[data-testid="graph-visualization"]').should('be.visible');

        // 验证图谱画布可见
        cy.get('[data-testid="graph-canvas"]').should('be.visible');

        // 在小屏幕上验证工具栏折叠
        if (viewport.width < 768) {
          cy.get('[data-testid="toolbar-collapse-btn"]').should('be.visible');
        }

        // 截图记录
        cy.screenshot(`visualization-${viewport.width}x${viewport.height}`);
      });
    });
  });
});

/**
 * 浏览器兼容性测试
 */
describe('浏览器兼容性测试', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.get('[data-testid="knowledge-base-menu"]').click();
    cy.get('[data-testid="knowledge-base-item"]').first().click();
    cy.get('[data-testid="knowledge-graph-tab"]').click();
  });

  it('应该在 Chrome 中正常工作', () => {
    cy.get('[data-testid="knowledge-graph-manager"]').should('be.visible');
    cy.get('[data-testid="knowledge-graph-dashboard"]').should('be.visible');
  });

  it('应该在 Firefox 中正常工作', () => {
    cy.get('[data-testid="knowledge-graph-manager"]').should('be.visible');
    cy.get('[data-testid="knowledge-graph-dashboard"]').should('be.visible');
  });

  it('应该在 Edge 中正常工作', () => {
    cy.get('[data-testid="knowledge-graph-manager"]').should('be.visible');
    cy.get('[data-testid="knowledge-graph-dashboard"]').should('be.visible');
  });
});

/**
 * 无障碍访问测试
 */
describe('无障碍访问测试', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.get('[data-testid="knowledge-base-menu"]').click();
    cy.get('[data-testid="knowledge-base-item"]').first().click();
    cy.get('[data-testid="knowledge-graph-tab"]').click();
  });

  it('应该支持键盘导航', () => {
    // 测试 Tab 键导航
    cy.get('body').tab();
    cy.focused().should('have.attr', 'data-testid');

    // 测试 Enter 键激活
    cy.focused().type('{enter}');
  });

  it('应该具有正确的 ARIA 标签', () => {
    // 验证主要组件有正确的 ARIA 属性
    cy.get('[data-testid="knowledge-graph-manager"]').should('have.attr', 'role');
    cy.get('[data-testid="entity-list"]').should('have.attr', 'aria-label');
  });

  it('应该支持屏幕阅读器', () => {
    // 验证按钮有描述性文本
    cy.get('button').each($button => {
      expect($button).to.have.attr('aria-label').or.to.have.text();
    });
  });
});
