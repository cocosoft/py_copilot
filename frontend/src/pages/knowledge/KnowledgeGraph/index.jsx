/**
 * 知识图谱页面
 *
 * 展示知识库的知识图谱可视化，支持实体识别和关系提取
 */

import React from 'react';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import HierarchyNavigator from '../../../components/Hierarchy/HierarchyNavigator';
import HierarchyViewContainer from '../../../components/Hierarchy/HierarchyViewContainer';
import './styles.css';

/**
 * 知识图谱页面
 */
const KnowledgeGraph = () => {
  const { currentKnowledgeBase } = useKnowledgeStore();

  return (
    <div className="knowledge-graph-page">
      <div className="page-header">
        <h2>知识图谱</h2>
        <p>可视化展示知识库中的实体和关系</p>
      </div>
      
      {/* 层级导航器 */}
      <HierarchyNavigator />
      
      {/* 层级视图容器 */}
      <div className="page-content">
        <HierarchyViewContainer knowledgeBaseId={currentKnowledgeBase?.id} />
      </div>
    </div>
  );
};

export default KnowledgeGraph;
