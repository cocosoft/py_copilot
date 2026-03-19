/**
 * 知识图谱页面
 *
 * 展示知识库的知识图谱可视化，支持实体识别和关系提取
 */

import React from 'react';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import EnhancedKnowledgeGraph from '../../../components/KnowledgeGraph/EnhancedKnowledgeGraph';
import './styles.css';

/**
 * 知识图谱页面
 */
const KnowledgeGraph = () => {
  const { currentKnowledgeBase } = useKnowledgeStore();

  /**
   * 处理节点点击
   */
  const handleNodeClick = (node) => {
    console.log('Node clicked:', node);
    // 可以在这里添加更多的节点点击处理逻辑
  };

  return (
    <div className="knowledge-graph-page">
      <EnhancedKnowledgeGraph 
        knowledgeBaseId={currentKnowledgeBase?.id}
        onNodeClick={handleNodeClick}
      />
    </div>
  );
};

export default KnowledgeGraph;
