/**
 * 实体关系管理页面
 *
 * 用于管理知识图谱中的实体关系，支持关系的增删改查操作
 */

import React from 'react';
import RelationManagement from '../../components/KnowledgeGraph/RelationManagement';
import useKnowledgeStore from '../../stores/knowledgeStore';

/**
 * 实体关系管理页面
 */
const EntityRelationships = () => {
  const { currentKnowledgeBase } = useKnowledgeStore();

  return (
    <div className="entity-relationships">
      <RelationManagement knowledgeBaseId={currentKnowledgeBase?.id} />
    </div>
  );
};

export default EntityRelationships;