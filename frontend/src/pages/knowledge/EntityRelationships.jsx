/**
 * 实体关系管理页面
 *
 * 用于管理知识图谱中的实体关系，支持关系的增删改查操作
 */

import React from 'react';
import { FiDatabase, FiLayers, FiFileText, FiGlobe } from 'lucide-react';
import HierarchyNavigator from '../../components/Hierarchy/HierarchyNavigator';
import HierarchyViewContainer from '../../components/Hierarchy/HierarchyViewContainer';
import useKnowledgeStore from '../../stores/knowledgeStore';

/**
 * 实体关系管理页面
 */
const EntityRelationships = () => {
  const { currentKnowledgeBase } = useKnowledgeStore();

  return (
    <div className="entity-relationships">
      <div className="page-header">
        <h1>实体关系管理</h1>
        <p>管理知识图谱中的实体关系，支持关系的增删改查操作</p>
      </div>
      
      <HierarchyNavigator />
      
      <div className="hierarchy-content">
        <HierarchyViewContainer knowledgeBaseId={currentKnowledgeBase?.id} />
      </div>
    </div>
  );
};

export default EntityRelationships;