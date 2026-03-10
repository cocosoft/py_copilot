/**
 * 三级知识图谱统一查看组件
 * 
 * 整合全局级、知识库级、文档级三层知识图谱的查看功能
 * 提供统一的界面切换和对比分析能力
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import KnowledgeGraph from '../KnowledgeGraph';
import knowledgeGraphApi from '../../services/knowledgeGraphApi';
import { showNotification, NotificationType } from '../UI/Notification';
import './HierarchicalGraphViewer.css';

/**
 * 层级类型定义
 */
const GRAPH_LEVELS = [
  {
    id: 'document',
    label: '文档级',
    icon: '📄',
    description: '单个文档内的实体和关系',
    color: '#4CAF50'
  },
  {
    id: 'knowledge_base',
    label: '知识库级',
    icon: '📚',
    description: '知识库内跨文档的实体对齐和关系',
    color: '#2196F3'
  },
  {
    id: 'global',
    label: '全局级',
    icon: '🌍',
    description: '跨知识库的全局实体和关系',
    color: '#9C27B0'
  }
];

/**
 * 三级知识图谱查看组件
 * 
 * @param {Object} props - 组件属性
 * @param {number} props.documentId - 文档ID（查看文档级时使用）
 * @param {number} props.knowledgeBaseId - 知识库ID（查看知识库级和文档级时使用）
 * @param {string} props.defaultLevel - 默认显示的层级
 * @param {boolean} props.showLevelSelector - 是否显示层级选择器
 * @param {boolean} props.showComparison - 是否显示对比模式
 * @param {Function} props.onNodeClick - 节点点击回调
 * @param {Function} props.onLevelChange - 层级切换回调
 */
const HierarchicalGraphViewer = ({
  documentId = null,
  knowledgeBaseId = null,
  defaultLevel = 'knowledge_base',
  showLevelSelector = true,
  showComparison = false,
  onNodeClick = null,
  onLevelChange = null
}) => {
  // 当前选中的层级
  const [currentLevel, setCurrentLevel] = useState(defaultLevel);
  
  // 图谱数据
  const [graphData, setGraphData] = useState({
    document: { nodes: [], edges: [] },
    knowledge_base: { nodes: [], edges: [] },
    global: { nodes: [], edges: [] }
  });
  
  // 加载状态
  const [loading, setLoading] = useState({
    document: false,
    knowledge_base: false,
    global: false
  });
  
  // 统计信息
  const [stats, setStats] = useState({
    document: null,
    knowledge_base: null,
    global: null
  });
  
  // 对比模式
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedLevelsForComparison, setSelectedLevelsForComparison] = useState([]);
  
  // 视图设置
  const [viewSettings, setViewSettings] = useState({
    layout: 'force', // force, hierarchical, circular
    showLabels: true,
    minConfidence: 0.5,
    entityTypes: [],
    relationTypes: []
  });

  /**
   * 加载指定层级的图谱数据
   */
  const loadGraphData = useCallback(async (level) => {
    if (loading[level]) return;
    
    setLoading(prev => ({ ...prev, [level]: true }));
    
    try {
      let response;
      
      switch (level) {
        case 'document':
          if (!documentId) {
            showNotification({
              title: '提示',
              message: '请先选择一个文档',
              type: NotificationType.WARNING
            });
            return;
          }
          response = await knowledgeGraphApi.getDocumentGraph(documentId);
          break;
          
        case 'knowledge_base':
          if (!knowledgeBaseId) {
            showNotification({
              title: '提示',
              message: '请先选择一个知识库',
              type: NotificationType.WARNING
            });
            return;
          }
          response = await knowledgeGraphApi.getGraphData(knowledgeBaseId, 'kb');
          break;
          
        case 'global':
          response = await knowledgeGraphApi.getGraphData(null, 'global');
          break;
          
        default:
          return;
      }
      
      // 检查API返回的错误
      if (response && response.success === false) {
        const errorMsg = response.error?.message || '未知错误';
        console.warn(`加载${level}级图谱数据返回错误:`, errorMsg);
        // 设置空数据
        setGraphData(prev => ({
          ...prev,
          [level]: { nodes: [], edges: [] }
        }));
        setStats(prev => ({
          ...prev,
          [level]: {
            nodeCount: 0,
            edgeCount: 0,
            entityTypes: [],
            relationTypes: []
          }
        }));
        return;
      }
      
      // 成功时直接使用返回的数据（格式：{nodes, edges, statistics}）
      if (response) {
        setGraphData(prev => ({
          ...prev,
          [level]: { nodes: response.nodes || [], edges: response.edges || [] }
        }));
        
        // 更新统计信息
        setStats(prev => ({
          ...prev,
          [level]: {
            nodeCount: response.nodes?.length || 0,
            edgeCount: response.edges?.length || 0,
            entityTypes: [...new Set(response.nodes?.map(n => n.type || n.entity_type) || [])],
            relationTypes: [...new Set(response.edges?.map(e => e.label || e.relation_type) || [])]
          }
        }));
      }
    } catch (error) {
      console.error(`加载${level}级图谱数据失败:`, error);
      showNotification({
        title: '加载失败',
        message: `加载${GRAPH_LEVELS.find(l => l.id === level)?.label}数据失败`,
        type: NotificationType.ERROR
      });
    } finally {
      setLoading(prev => ({ ...prev, [level]: false }));
    }
  }, [documentId, knowledgeBaseId, loading]);

  /**
   * 切换层级
   */
  const handleLevelChange = (level) => {
    setCurrentLevel(level);
    
    // 如果数据未加载，自动加载
    if (graphData[level].nodes.length === 0 && !loading[level]) {
      loadGraphData(level);
    }
    
    if (onLevelChange) {
      onLevelChange(level);
    }
  };

  /**
   * 刷新当前层级数据
   */
  const handleRefresh = () => {
    loadGraphData(currentLevel);
  };

  /**
   * 切换对比模式
   */
  const toggleComparisonMode = () => {
    setComparisonMode(!comparisonMode);
    if (!comparisonMode) {
      // 开启对比模式时，默认选中当前层级和下一层级
      const currentIndex = GRAPH_LEVELS.findIndex(l => l.id === currentLevel);
      const nextLevel = GRAPH_LEVELS[(currentIndex + 1) % GRAPH_LEVELS.length];
      setSelectedLevelsForComparison([currentLevel, nextLevel.id]);
    }
  };

  /**
   * 选择对比层级
   */
  const toggleLevelForComparison = (level) => {
    setSelectedLevelsForComparison(prev => {
      if (prev.includes(level)) {
        return prev.filter(l => l !== level);
      }
      if (prev.length >= 2) {
        return [prev[1], level];
      }
      return [...prev, level];
    });
  };

  /**
   * 渲染层级选择器
   */
  const renderLevelSelector = () => (
    <div className="level-selector">
      {GRAPH_LEVELS.map(level => {
        const isActive = currentLevel === level.id;
        const isAvailable = level.id === 'global' || 
          (level.id === 'knowledge_base' && knowledgeBaseId) ||
          (level.id === 'document' && (documentId || knowledgeBaseId));
        
        return (
          <button
            key={level.id}
            className={`level-btn ${isActive ? 'active' : ''} ${!isAvailable ? 'disabled' : ''}`}
            onClick={() => isAvailable && handleLevelChange(level.id)}
            disabled={!isAvailable}
            title={level.description}
          >
            <span className="level-icon">{level.icon}</span>
            <span className="level-label">{level.label}</span>
            {stats[level.id] && (
              <span className="level-badge">
                {stats[level.id].nodeCount}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );

  /**
   * 渲染统计信息面板
   */
  const renderStatsPanel = () => {
    const currentStats = stats[currentLevel];
    if (!currentStats) return null;
    
    return (
      <div className="stats-panel">
        <div className="stat-item">
          <span className="stat-icon">🔵</span>
          <div className="stat-info">
            <span className="stat-value">{currentStats.nodeCount}</span>
            <span className="stat-label">实体</span>
          </div>
        </div>
        <div className="stat-item">
          <span className="stat-icon">🔗</span>
          <div className="stat-info">
            <span className="stat-value">{currentStats.edgeCount}</span>
            <span className="stat-label">关系</span>
          </div>
        </div>
        <div className="stat-item">
          <span className="stat-icon">🏷️</span>
          <div className="stat-info">
            <span className="stat-value">{currentStats.entityTypes.length}</span>
            <span className="stat-label">实体类型</span>
          </div>
        </div>
        <div className="stat-item">
          <span className="stat-icon">↔️</span>
          <div className="stat-info">
            <span className="stat-value">{currentStats.relationTypes.length}</span>
            <span className="stat-label">关系类型</span>
          </div>
        </div>
      </div>
    );
  };

  /**
   * 渲染工具栏
   */
  const renderToolbar = () => (
    <div className="graph-toolbar">
      <div className="toolbar-left">
        {showComparison && (
          <button
            className={`toolbar-btn ${comparisonMode ? 'active' : ''}`}
            onClick={toggleComparisonMode}
            title="对比模式"
          >
            📊 对比
          </button>
        )}
        <button
          className="toolbar-btn"
          onClick={handleRefresh}
          disabled={loading[currentLevel]}
          title="刷新数据"
        >
          {loading[currentLevel] ? '⏳' : '🔄'} 刷新
        </button>
      </div>
      
      <div className="toolbar-right">
        <select
          className="view-select"
          value={viewSettings.layout}
          onChange={(e) => setViewSettings(prev => ({ ...prev, layout: e.target.value }))}
        >
          <option value="force">力导向布局</option>
          <option value="hierarchical">层次布局</option>
          <option value="circular">环形布局</option>
        </select>
        
        <label className="toolbar-checkbox">
          <input
            type="checkbox"
            checked={viewSettings.showLabels}
            onChange={(e) => setViewSettings(prev => ({ ...prev, showLabels: e.target.checked }))}
          />
          显示标签
        </label>
      </div>
    </div>
  );

  /**
   * 渲染图谱可视化
   */
  const renderGraphVisualization = (level, isComparison = false) => {
    const data = graphData[level];
    const levelInfo = GRAPH_LEVELS.find(l => l.id === level);
    
    if (loading[level]) {
      return (
        <div className="graph-loading">
          <div className="loading-spinner"></div>
          <p>正在加载{levelInfo?.label}数据...</p>
        </div>
      );
    }
    
    if (data.nodes.length === 0) {
      return (
        <div className="graph-empty">
          <span className="empty-icon">📭</span>
          <p>暂无{levelInfo?.label}数据</p>
          <button
            className="load-btn"
            onClick={() => loadGraphData(level)}
          >
            加载数据
          </button>
        </div>
      );
    }
    
    return (
      <div className={`graph-view ${isComparison ? 'comparison-view' : ''}`}>
        {isComparison && (
          <div className="view-header" style={{ borderColor: levelInfo?.color }}>
            <span className="view-icon">{levelInfo?.icon}</span>
            <span className="view-title">{levelInfo?.label}</span>
            <span className="view-count">{data.nodes.length} 实体</span>
          </div>
        )}
        <div className="graph-container">
          <KnowledgeGraph
            graphData={data}
            width={null}
            height={null}
            layout={viewSettings.layout}
            showLabels={viewSettings.showLabels}
            onNodeClick={onNodeClick}
          />
        </div>
      </div>
    );
  };

  /**
   * 渲染对比视图
   */
  const renderComparisonView = () => (
    <div className="comparison-container">
      <div className="comparison-selector">
        <p>选择要对比的层级（最多2个）：</p>
        <div className="comparison-levels">
          {GRAPH_LEVELS.map(level => {
            const isSelected = selectedLevelsForComparison.includes(level.id);
            const isAvailable = level.id === 'global' || 
              (level.id === 'knowledge_base' && knowledgeBaseId) ||
              (level.id === 'document' && documentId);
            
            return (
              <label
                key={level.id}
                className={`comparison-level ${isSelected ? 'selected' : ''} ${!isAvailable ? 'disabled' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => isAvailable && toggleLevelForComparison(level.id)}
                  disabled={!isAvailable}
                />
                <span className="level-icon">{level.icon}</span>
                <span className="level-label">{level.label}</span>
              </label>
            );
          })}
        </div>
      </div>
      
      {selectedLevelsForComparison.length === 2 && (
        <div className="comparison-views">
          {selectedLevelsForComparison.map(level => (
            <div key={level} className="comparison-panel">
              {renderGraphVisualization(level, true)}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // 初始加载默认层级数据
  useEffect(() => {
    if (graphData[defaultLevel].nodes.length === 0) {
      loadGraphData(defaultLevel);
    }
  }, [defaultLevel, loadGraphData]);

  return (
    <div className="hierarchical-graph-viewer">
      {/* 层级选择器 */}
      {showLevelSelector && renderLevelSelector()}
      
      {/* 工具栏 */}
      {renderToolbar()}
      
      {/* 统计信息 */}
      {renderStatsPanel()}
      
      {/* 主内容区 */}
      <div className="viewer-content">
        {comparisonMode && showComparison ? (
          renderComparisonView()
        ) : (
          renderGraphVisualization(currentLevel)
        )}
      </div>
      
      {/* 层级说明 */}
      <div className="level-info">
        <div 
          className="info-card"
          style={{ borderLeftColor: GRAPH_LEVELS.find(l => l.id === currentLevel)?.color }}
        >
          <h4>
            {GRAPH_LEVELS.find(l => l.id === currentLevel)?.icon}
            {GRAPH_LEVELS.find(l => l.id === currentLevel)?.label}
          </h4>
          <p>{GRAPH_LEVELS.find(l => l.id === currentLevel)?.description}</p>
        </div>
      </div>
    </div>
  );
};

HierarchicalGraphViewer.propTypes = {
  documentId: PropTypes.number,
  knowledgeBaseId: PropTypes.number,
  defaultLevel: PropTypes.oneOf(['document', 'knowledge_base', 'global']),
  showLevelSelector: PropTypes.bool,
  showComparison: PropTypes.bool,
  onNodeClick: PropTypes.func,
  onLevelChange: PropTypes.func
};

export default HierarchicalGraphViewer;
