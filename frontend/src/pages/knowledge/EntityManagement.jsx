/**
 * 实体管理页面
 *
 * 整合实体识别和实体关系管理功能，提供统一的实体管理界面
 */

import React from 'react';
import useKnowledgeStore from '@stores/knowledgeStore';
import HierarchyNavigator from '../../components/Hierarchy/HierarchyNavigator';
import HierarchyViewContainer from '../../components/Hierarchy/HierarchyViewContainer';
import './EntityManagement.css';

/**
 * 实体管理页面
 */
const EntityManagement = () => {
  const { currentKnowledgeBase } = useKnowledgeStore();

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