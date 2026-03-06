/**
 * 图谱可视化组件
 *
 * 提供知识图谱的可视化展示功能，复用现有的 KnowledgeGraph 组件
 */

import React, { useState, useEffect } from 'react';
import KnowledgeGraph from '../KnowledgeGraph';
import './GraphVisualization.css';

/**
 * 图谱可视化组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @returns {JSX.Element} 图谱可视化界面
 */
const GraphVisualization = ({ knowledgeBaseId }) => {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('force'); // force, hierarchical
  const [filters, setFilters] = useState({
    entityTypes: [],
    relationTypes: [],
    minConfidence: 0.5
  });

  // 加载图谱数据
  useEffect(() => {
    if (!knowledgeBaseId) return;

    setLoading(true);
    // TODO: 调用API获取图谱数据
    // Mock数据
    setTimeout(() => {
      setGraphData({
        nodes: [
          { id: 1, name: '张三', type: 'PERSON', confidence: 0.95 },
          { id: 2, name: 'ABC公司', type: 'ORG', confidence: 0.92 },
          { id: 3, name: '北京', type: 'LOCATION', confidence: 0.98 },
          { id: 4, name: '李四', type: 'PERSON', confidence: 0.91 },
          { id: 5, name: 'XYZ科技', type: 'ORG', confidence: 0.89 }
        ],
        edges: [
          { source: 1, target: 2, type: '就职于', confidence: 0.88 },
          { source: 2, target: 3, type: '位于', confidence: 0.95 },
          { source: 4, target: 2, type: '就职于', confidence: 0.85 },
          { source: 1, target: 4, type: '同事', confidence: 0.78 }
        ]
      });
      setLoading(false);
    }, 1000);
  }, [knowledgeBaseId]);

  if (loading) {
    return (
      <div className="graph-visualization-loading">
        <div className="spinner"></div>
        <p>加载图谱数据...</p>
      </div>
    );
  }

  return (
    <div className="graph-visualization">
      {/* 工具栏 */}
      <div className="visualization-toolbar">
        <div className="view-modes">
          <button 
            className={`mode-btn ${viewMode === 'force' ? 'active' : ''}`}
            onClick={() => setViewMode('force')}
          >
            力导向图
          </button>
          <button 
            className={`mode-btn ${viewMode === 'hierarchical' ? 'active' : ''}`}
            onClick={() => setViewMode('hierarchical')}
          >
            层次图
          </button>
        </div>

        <div className="graph-actions">
          <button className="action-btn">
            🔍 放大
          </button>
          <button className="action-btn">
            🔎 缩小
          </button>
          <button className="action-btn">
            ⟲ 重置
          </button>
        </div>
      </div>

      {/* 筛选面板 */}
      <div className="filter-panel">
        <h4>筛选条件</h4>
        <div className="filter-group">
          <label>最小置信度: {(filters.minConfidence * 100).toFixed(0)}%</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={filters.minConfidence}
            onChange={(e) => setFilters({...filters, minConfidence: parseFloat(e.target.value)})}
          />
        </div>
      </div>

      {/* 图谱展示区域 */}
      <div className="graph-container">
        {graphData.nodes.length > 0 ? (
          <KnowledgeGraph 
            data={graphData}
            viewMode={viewMode}
            filters={filters}
          />
        ) : (
          <div className="empty-graph">
            <span className="empty-icon">🕸️</span>
            <p>暂无图谱数据</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GraphVisualization;
