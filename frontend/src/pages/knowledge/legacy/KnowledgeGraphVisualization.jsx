/**
 * 知识图谱可视化页面
 * 
 * 提供完整的知识图谱可视化功能，包括：
 * - 分层图谱展示
 * - 实体搜索
 * - 关系过滤
 * - 实体详情查看
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import HierarchicalGraphVisualizer, { LayerType } from '@components/knowledgeGraph/HierarchicalGraphVisualizer';
import { getKnowledgeBaseGraphStats } from '@utils/api/knowledgeGraphApi';
import './KnowledgeGraphVisualization.css';

/**
 * 知识图谱可视化页面
 */
const KnowledgeGraphVisualization = () => {
  const { knowledgeBaseId } = useParams();
  const navigate = useNavigate();
  
  // 状态管理
  const [currentLayer, setCurrentLayer] = useState(LayerType.DOCUMENT);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntityTypes, setSelectedEntityTypes] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [graphStats, setGraphStats] = useState({
    totalEntities: 0,
    totalRelationships: 0,
    entityTypes: []
  });

  // 实体类型选项
  const entityTypeOptions = [
    { value: 'PERSON', label: '人物', color: '#5470c6' },
    { value: 'ORGANIZATION', label: '组织', color: '#91cc75' },
    { value: 'LOCATION', label: '地点', color: '#fac858' },
    { value: 'PRODUCT', label: '产品', color: '#ee6666' },
    { value: 'EVENT', label: '事件', color: '#73c0de' }
  ];

  /**
   * 加载图谱统计信息
   */
  useEffect(() => {
    const loadGraphStats = async () => {
      try {
        // 调用真实 API 获取图谱统计
        const stats = await getKnowledgeBaseGraphStats(parseInt(knowledgeBaseId));

        // 转换后端数据为前端格式
        const entityTypes = Object.entries(stats.entity_types || {}).map(([type, count]) => ({
          type,
          count
        }));

        setGraphStats({
          totalEntities: stats.total_entities || 0,
          totalRelationships: stats.total_relationships || 0,
          entityTypes: entityTypes
        });
      } catch (error) {
        console.error('加载图谱统计失败:', error);
      }
    };

    if (knowledgeBaseId) {
      loadGraphStats();
    }
  }, [knowledgeBaseId]);

  /**
   * 处理节点点击
   */
  const handleNodeClick = useCallback((nodeData) => {
    setSelectedNode(nodeData);
    setIsDetailModalOpen(true);
  }, []);

  /**
   * 处理图层切换
   */
  const handleLayerChange = useCallback((layer) => {
    setCurrentLayer(layer);
    setSelectedNode(null);
  }, []);

  /**
   * 处理实体类型过滤
   */
  const handleEntityTypeToggle = (type) => {
    setSelectedEntityTypes(prev => {
      if (prev.includes(type)) {
        return prev.filter(t => t !== type);
      }
      return [...prev, type];
    });
  };

  /**
   * 处理搜索
   */
  const handleSearch = (e) => {
    e.preventDefault();
    // 实际项目中应该调用搜索API
    console.log('搜索:', searchQuery);
  };

  /**
   * 关闭详情弹窗
   */
  const closeDetailModal = () => {
    setIsDetailModalOpen(false);
    setSelectedNode(null);
  };

  /**
   * 导出图谱数据
   */
  const handleExport = () => {
    // 实际项目中应该调用导出API
    console.log('导出图谱数据');
  };

  /**
   * 刷新图谱
   */
  const handleRefresh = () => {
    // 实际项目中应该重新加载数据
    console.log('刷新图谱');
  };

  return (
    <div className="knowledge-graph-visualization-page">
      {/* 页面头部 */}
      <div className="page-header">
        <div className="header-left">
          <button 
            className="back-btn"
            onClick={() => navigate('/knowledge')}
          >
            ← 返回
          </button>
          <h1>知识图谱可视化</h1>
          <span className="knowledge-base-id">知识库: {knowledgeBaseId}</span>
        </div>
        <div className="header-actions">
          <button className="action-btn" onClick={handleRefresh}>
            🔄 刷新
          </button>
          <button className="action-btn primary" onClick={handleExport}>
            📥 导出
          </button>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="page-content">
        {/* 左侧边栏 */}
        <div className="sidebar">
          {/* 搜索框 */}
          <div className="sidebar-section">
            <h3>实体搜索</h3>
            <form onSubmit={handleSearch} className="search-form">
              <input
                type="text"
                placeholder="搜索实体..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <button type="submit" className="search-btn">
                🔍
              </button>
            </form>
          </div>

          {/* 实体类型过滤 */}
          <div className="sidebar-section">
            <h3>实体类型过滤</h3>
            <div className="entity-type-filters">
              {entityTypeOptions.map(type => (
                <label key={type.value} className="filter-item">
                  <input
                    type="checkbox"
                    checked={selectedEntityTypes.includes(type.value)}
                    onChange={() => handleEntityTypeToggle(type.value)}
                  />
                  <span 
                    className="type-color"
                    style={{ backgroundColor: type.color }}
                  />
                  <span className="type-label">{type.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 统计信息 */}
          <div className="sidebar-section">
            <h3>统计信息</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-number">{graphStats.totalEntities}</span>
                <span className="stat-label">总实体</span>
              </div>
              <div className="stat-card">
                <span className="stat-number">{graphStats.totalRelationships}</span>
                <span className="stat-label">总关系</span>
              </div>
            </div>
            <div className="entity-type-stats">
              {graphStats.entityTypes.map(item => {
                const typeInfo = entityTypeOptions.find(t => t.value === item.type);
                return (
                  <div key={item.type} className="type-stat-row">
                    <span 
                      className="type-dot"
                      style={{ backgroundColor: typeInfo?.color }}
                    />
                    <span className="type-name">{typeInfo?.label}</span>
                    <span className="type-count">{item.count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 图例说明 */}
          <div className="sidebar-section">
            <h3>图例说明</h3>
            <div className="legend-list">
              <div className="legend-item">
                <span className="legend-symbol node" />
                <span>实体节点</span>
              </div>
              <div className="legend-item">
                <span className="legend-symbol edge" />
                <span>关系边</span>
              </div>
              <div className="legend-item">
                <span className="legend-symbol size" />
                <span>节点大小 = 重要性</span>
              </div>
            </div>
          </div>
        </div>

        {/* 可视化区域 */}
        <div className="visualization-area">
          <HierarchicalGraphVisualizer
            knowledgeBaseId={knowledgeBaseId}
            currentLayer={currentLayer}
            onNodeClick={handleNodeClick}
            onLayerChange={handleLayerChange}
            width="100%"
            height="calc(100vh - 200px)"
          />
        </div>
      </div>

      {/* 实体详情弹窗 */}
      {isDetailModalOpen && selectedNode && (
        <div className="modal-overlay" onClick={closeDetailModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>实体详情</h2>
              <button className="close-btn" onClick={closeDetailModal}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h4>基本信息</h4>
                <div className="detail-row">
                  <span className="detail-label">名称:</span>
                  <span className="detail-value">{selectedNode.name}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">类型:</span>
                  <span className="detail-value">{selectedNode.entityType}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">ID:</span>
                  <span className="detail-value">{selectedNode.id}</span>
                </div>
                {selectedNode.confidence && (
                  <div className="detail-row">
                    <span className="detail-label">置信度:</span>
                    <span className="detail-value">
                      {(selectedNode.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
                {selectedNode.importance && (
                  <div className="detail-row">
                    <span className="detail-label">重要性:</span>
                    <span className="detail-value">
                      {(selectedNode.importance * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>

              {selectedNode.alignedEntities && (
                <div className="detail-section">
                  <h4>对齐实体</h4>
                  <ul className="aligned-list">
                    {selectedNode.alignedEntities.map((entity, idx) => (
                      <li key={idx}>{entity}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="detail-actions">
                <button className="action-btn">
                  查看相关实体
                </button>
                <button className="action-btn">
                  编辑实体
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraphVisualization;
