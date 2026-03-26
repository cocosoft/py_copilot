/**
 * 实体管理页面
 *
 * 整合实体识别和实体关系管理功能，提供统一的实体管理界面
 */

import React from 'react';
import useKnowledgeBaseValidation from '../../hooks/useKnowledgeBaseValidation';
import EmptyKnowledgeBaseState from '../../components/Knowledge/EmptyKnowledgeBaseState';
import HierarchyNavigator from '../../components/Hierarchy/HierarchyNavigator';
import HierarchyViewContainer from '../../components/Hierarchy/HierarchyViewContainer';
import './EntityManagement.css';

/**
 * 实体管理页面
 */
const EntityManagement = () => {
  const { isValid, isChecking, currentKnowledgeBase } = useKnowledgeBaseValidation();

  // 验证中，显示加载状态
  if (isChecking) {
    return (
      <div className="entity-management">
        <div className="entity-management-header">
          <h2>实体管理</h2>
          <p>管理知识库中的实体和实体关系</p>
        </div>
        <div className="entity-management-loading">
          <div className="loading-spinner"></div>
          <p>正在加载知识库...</p>
        </div>
      </div>
    );
  }

  // 知识库不存在时显示引导界面
  if (!isValid) {
    return (
      <div className="entity-management">
        <div className="entity-management-header">
          <h2>实体管理</h2>
          <p>管理知识库中的实体和实体关系</p>
        </div>
        <EmptyKnowledgeBaseState
          title="暂无知识库"
          description="您还没有创建任何知识库，请先创建知识库后再管理实体"
        />
      </div>
    );
  }

  return (
    <div className="entity-management">
      <div className="entity-management-header">
        <h2>实体管理</h2>
        <p>管理知识库中的实体和实体关系</p>
      </div>

      {/* 层级视图容器 */}
      <div className="entity-management-content">
        <HierarchyViewContainer knowledgeBaseId={currentKnowledgeBase?.id} />
      </div>
    </div>
  );
};

export default EntityManagement;