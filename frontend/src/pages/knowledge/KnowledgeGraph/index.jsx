/**
 * 知识图谱页面
 *
 * 展示知识库的知识图谱可视化，支持实体识别和关系提取
 */

import React from 'react';
import useKnowledgeBaseValidation from '../../../hooks/useKnowledgeBaseValidation';
import EmptyKnowledgeBaseState from '../../../components/Knowledge/EmptyKnowledgeBaseState';
import HierarchyNavigator from '../../../components/Hierarchy/HierarchyNavigator';
import HierarchyViewContainer from '../../../components/Hierarchy/HierarchyViewContainer';
import './styles.css';

/**
 * 知识图谱页面
 */
const KnowledgeGraph = () => {
  const { isValid, isChecking, currentKnowledgeBase } = useKnowledgeBaseValidation();

  // 验证中，显示加载状态
  if (isChecking) {
    return (
      <div className="knowledge-graph-page">
        <div className="page-header">
          <h2>知识图谱</h2>
          <p>可视化展示知识库中的实体和关系</p>
        </div>
        <div className="page-loading">
          <div className="loading-spinner"></div>
          <p>正在加载知识库...</p>
        </div>
      </div>
    );
  }

  // 知识库不存在时显示引导界面
  if (!isValid) {
    return (
      <div className="knowledge-graph-page">
        <div className="page-header">
          <h2>知识图谱</h2>
          <p>可视化展示知识库中的实体和关系</p>
        </div>
        <EmptyKnowledgeBaseState
          title="暂无知识库"
          description="您还没有创建任何知识库，请先创建知识库后再查看知识图谱"
        />
      </div>
    );
  }

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
