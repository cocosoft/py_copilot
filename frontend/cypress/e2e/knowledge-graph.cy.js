/**
 * 知识图谱功能端到端测试
 * 
 * 功能：测试知识图谱管理功能的完整流程
 */

describe('知识图谱管理功能测试', () => {
  beforeEach(() => {
    // 登录并导航到知识库页面
    cy.visit('/');
    cy.get('[data-testid="knowledge-base-menu"]').click();
  });

  describe('知识库管理页面', () => {
    it('应该显示知识库列表', () => {
      cy.get('[data-testid="knowledge-base-list"]').should('be.visible');
      cy.get('[data-testid="knowledge-base-item"]').should('have.length.at.least', 1);
    });

    it('应该能进入知识库详情', () => {
      cy.get('[data-testid="knowledge-base-item"]').first().click();
      cy.get('[data-testid="knowledge-base-detail"]').should('be.visible');
    });
  });

  describe('知识图谱管理', () => {
    beforeEach(() => {
      // 进入知识库详情
      cy.get('[data-testid="knowledge-base-item"]').first().click();
      // 切换到知识图谱标签
      cy.get('[data-testid="knowledge-graph-tab"]').click();
    });

    it('应该显示知识图谱管理界面', () => {
      cy.get('[data-testid="knowledge-graph-manager"]').should('be.visible');
    });

    it('应该显示知识图谱统计信息', () => {
      cy.get('[data-testid="knowledge-graph-dashboard"]').should('be.visible');
      cy.get('[data-testid="entity-count"]').should('be.visible');
      cy.get('[data-testid="relation-count"]').should('be.visible');
    });

    it('应该能切换到实体管理标签', () => {
      cy.get('[data-testid="entity-management-tab"]').click();
      cy.get('[data-testid="entity-management"]').should('be.visible');
      cy.get('[data-testid="entity-list"]').should('be.visible');
    });

    it('应该能切换到批量构建标签', () => {
      cy.get('[data-testid="batch-build-tab"]').click();
      cy.get('[data-testid="batch-build-panel"]').should('be.visible');
    });

    it('应该能切换到可视化标签', () => {
      cy.get('[data-testid="visualization-tab"]').click();
      cy.get('[data-testid="graph-visualization"]').should('be.visible');
    });
  });

  describe('实体管理功能', () => {
    beforeEach(() => {
      cy.get('[data-testid="knowledge-base-item"]').first().click();
      cy.get('[data-testid="knowledge-graph-tab"]').click();
      cy.get('[data-testid="entity-management-tab"]').click();
    });

    it('应该能搜索实体', () => {
      cy.get('[data-testid="entity-search-input"]').type('测试');
      cy.get('[data-testid="entity-list"]').should('be.visible');
    });

    it('应该能筛选实体类型', () => {
      cy.get('[data-testid="entity-type-filter"]').select('人物');
      cy.get('[data-testid="entity-list"]').should('be.visible');
    });

    it('应该能选择实体', () => {
      cy.get('[data-testid="entity-checkbox"]').first().click();
      cy.get('[data-testid="batch-actions-bar"]').should('be.visible');
    });

    it('应该能批量删除实体', () => {
      // 选择多个实体
      cy.get('[data-testid="entity-checkbox"]').eq(0).click();
      cy.get('[data-testid="entity-checkbox"]').eq(1).click();

      // 点击批量删除
      cy.get('[data-testid="batch-delete-btn"]').click();

      // 确认删除
      cy.get('[data-testid="confirm-dialog"]').should('be.visible');
      cy.get('[data-testid="confirm-btn"]').click();

      // 验证删除成功提示
      cy.get('[data-testid="success-message"]').should('be.visible');
    });

    it('应该能导出实体', () => {
      cy.get('[data-testid="export-btn"]').click();
      cy.get('[data-testid="export-dialog"]').should('be.visible');
      cy.get('[data-testid="export-confirm-btn"]').click();
    });
  });

  describe('批量构建功能', () => {
    beforeEach(() => {
      cy.get('[data-testid="knowledge-base-item"]').first().click();
      cy.get('[data-testid="knowledge-graph-tab"]').click();
      cy.get('[data-testid="batch-build-tab"]').click();
    });

    it('应该显示可构建的文档列表', () => {
      cy.get('[data-testid="document-list"]').should('be.visible');
    });

    it('应该能选择文档', () => {
      cy.get('[data-testid="document-checkbox"]').first().click();
      cy.get('[data-testid="selected-count"]').should('contain', '已选择 1 个文档');
    });

    it('应该能全选文档', () => {
      cy.get('[data-testid="select-all-checkbox"]').click();
      cy.get('[data-testid="selected-count"]').should('contain', '已选择');
    });

    it('应该能启动批量构建', () => {
      // 选择文档
      cy.get('[data-testid="document-checkbox"]').first().click();

      // 点击开始构建
      cy.get('[data-testid="start-build-btn"]').click();

      // 验证进度显示
      cy.get('[data-testid="build-progress"]').should('be.visible');
    });

    it('应该能取消构建', () => {
      // 选择文档并启动构建
      cy.get('[data-testid="document-checkbox"]').first().click();
      cy.get('[data-testid="start-build-btn"]').click();

      // 等待进度显示
      cy.get('[data-testid="build-progress"]').should('be.visible');

      // 点击取消
      cy.get('[data-testid="cancel-build-btn"]').click();

      // 验证取消成功
      cy.get('[data-testid="build-progress"]').should('not.exist');
    });
  });

  describe('知识图谱可视化', () => {
    beforeEach(() => {
      cy.get('[data-testid="knowledge-base-item"]').first().click();
      cy.get('[data-testid="knowledge-graph-tab"]').click();
      cy.get('[data-testid="visualization-tab"]').click();
    });

    it('应该显示知识图谱可视化', () => {
      cy.get('[data-testid="graph-visualization"]').should('be.visible');
      cy.get('[data-testid="graph-canvas"]').should('be.visible');
    });

    it('应该能进行社区发现分析', () => {
      cy.get('[data-testid="community-analysis-btn"]').click();
      cy.get('[data-testid="analysis-panel"]').should('be.visible');
      cy.get('[data-testid="community-result"]').should('be.visible');
    });

    it('应该能进行中心性分析', () => {
      cy.get('[data-testid="centrality-analysis-btn"]').click();
      cy.get('[data-testid="analysis-panel"]').should('be.visible');
      cy.get('[data-testid="centrality-result"]').should('be.visible');
    });

    it('应该能查找路径', () => {
      // 选择起始实体
      cy.get('[data-testid="path-start-select"]').select('张三');
      // 选择目标实体
      cy.get('[data-testid="path-end-select"]').select('李四');
      // 点击查找
      cy.get('[data-testid="find-path-btn"]').click();

      // 验证路径结果显示
      cy.get('[data-testid="path-result"]').should('be.visible');
    });

    it('应该能重置视图', () => {
      cy.get('[data-testid="reset-view-btn"]').click();
      cy.get('[data-testid="graph-canvas"]').should('be.visible');
    });
  });

  describe('文档级实体确认', () => {
    beforeEach(() => {
      // 进入文档详情页面
      cy.get('[data-testid="knowledge-base-item"]').first().click();
      cy.get('[data-testid="document-item"]').first().click();
    });

    it('应该显示文档详情', () => {
      cy.get('[data-testid="document-detail"]').should('be.visible');
    });

    it('应该能切换到知识图谱标签', () => {
      cy.get('[data-testid="knowledge-graph-tab"]').click();
      cy.get('[data-testid="knowledge-graph-layout"]').should('be.visible');
    });

    it('应该显示实体确认列表', () => {
      cy.get('[data-testid="knowledge-graph-tab"]').click();
      cy.get('[data-testid="entity-confirmation-list"]').should('be.visible');
    });

    it('应该能确认实体', () => {
      cy.get('[data-testid="knowledge-graph-tab"]').click();

      // 找到待确认的实体
      cy.get('[data-testid="entity-item"]').first().within(() => {
        cy.get('[data-testid="confirm-btn"]').click();
      });

      // 验证状态变为已确认
      cy.get('[data-testid="entity-status"]').first().should('contain', '已确认');
    });

    it('应该能拒绝实体', () => {
      cy.get('[data-testid="knowledge-graph-tab"]').click();

      // 找到待确认的实体
      cy.get('[data-testid="entity-item"]').first().within(() => {
        cy.get('[data-testid="reject-btn"]').click();
      });

      // 验证状态变为已拒绝
      cy.get('[data-testid="entity-status"]').first().should('contain', '已拒绝');
    });

    it('应该能编辑实体', () => {
      cy.get('[data-testid="knowledge-graph-tab"]').click();

      // 点击编辑按钮
      cy.get('[data-testid="entity-item"]').first().within(() => {
        cy.get('[data-testid="edit-btn"]').click();
      });

      // 验证编辑表单显示
      cy.get('[data-testid="entity-edit-form"]').should('be.visible');

      // 修改实体名称
      cy.get('[data-testid="entity-name-input"]').clear().type('新名称');

      // 保存修改
      cy.get('[data-testid="save-btn"]').click();

      // 验证修改成功
      cy.get('[data-testid="success-message"]').should('be.visible');
    });

    it('应该能高亮实体在原文中的位置', () => {
      cy.get('[data-testid="knowledge-graph-tab"]').click();

      // 点击实体名称
      cy.get('[data-testid="entity-name"]').first().click();

      // 验证原文高亮
      cy.get('[data-testid="highlighted-text"]').should('be.visible');
    });

    it('应该能重新提取实体', () => {
      cy.get('[data-testid="knowledge-graph-tab"]').click();

      // 点击重新提取按钮
      cy.get('[data-testid="reextract-btn"]').click();

      // 确认重新提取
      cy.get('[data-testid="confirm-dialog"]').should('be.visible');
      cy.get('[data-testid="confirm-btn"]').click();

      // 验证重新提取成功
      cy.get('[data-testid="success-message"]').should('be.visible');
    });
  });

  describe('设置页面 - 知识图谱配置', () => {
    beforeEach(() => {
      cy.get('[data-testid="settings-menu"]').click();
      cy.get('[data-testid="knowledge-graph-config-menu"]').click();
    });

    it('应该显示知识图谱配置页面', () => {
      cy.get('[data-testid="knowledge-graph-config"]').should('be.visible');
    });

    it('应该能配置实体类型', () => {
      cy.get('[data-testid="entity-types-tab"]').click();
      cy.get('[data-testid="entity-types-list"]').should('be.visible');
    });

    it('应该能配置关系类型', () => {
      cy.get('[data-testid="relation-types-tab"]').click();
      cy.get('[data-testid="relation-types-list"]').should('be.visible');
    });

    it('应该能添加新的关系类型', () => {
      cy.get('[data-testid="relation-types-tab"]').click();
      cy.get('[data-testid="add-relation-type-btn"]').click();

      // 填写关系类型信息
      cy.get('[data-testid="relation-name-input"]').type('测试关系');
      cy.get('[data-testid="relation-color-input"]').type('#ff0000');

      // 保存
      cy.get('[data-testid="save-btn"]').click();

      // 验证添加成功
      cy.get('[data-testid="success-message"]').should('be.visible');
    });
  });
});
