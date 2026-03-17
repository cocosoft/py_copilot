/**
 * 融合版知识图谱组件
 * 
 * 结合 EnhancedKnowledgeGraph 和 KnowledgeGraph 页面的优点：
 * - 从知识库加载真实数据
 * - D3.js 力导向图可视化
 * - 丰富的交互功能
 * - 知识图谱构建功能
 */

import React, { useEffect, useCallback, useState, useRef } from 'react';
import * as d3 from 'd3';
import { 
  FiRefreshCw, 
  FiZoomIn, 
  FiZoomOut, 
  FiMaximize, 
  FiFilter, 
  FiCpu, 
  FiCheckCircle, 
  FiAlertCircle,
  FiSearch,
  FiDownload
} from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { message } from '../../../components/UI/Message/Message';
import {
  getKnowledgeBaseGraphData,
  buildKnowledgeGraph
} from '../../../utils/api/knowledgeApi';
import './UnifiedKnowledgeGraph.css';

/**
 * 实体类型配置
 */
const ENTITY_CONFIG = {
  'PERSON': { color: '#FF6B6B', icon: '👤', label: '人物', size: 35 },
  'ORGANIZATION': { color: '#4ECDC4', icon: '🏢', label: '组织', size: 40 },
  'ORG': { color: '#4ECDC4', icon: '🏢', label: '组织', size: 40 },
  'LOCATION': { color: '#45B7D1', icon: '📍', label: '地点', size: 32 },
  'LOC': { color: '#45B7D1', icon: '📍', label: '地点', size: 32 },
  'DATE': { color: '#96CEB4', icon: '📅', label: '日期', size: 28 },
  'MONEY': { color: '#FECA57', icon: '💰', label: '金额', size: 30 },
  'TECH': { color: '#A29BFE', icon: '💻', label: '技术', size: 32 },
  'PRODUCT': { color: '#FD79A8', icon: '📦', label: '产品', size: 32 },
  'EVENT': { color: '#FDCB6E', icon: '📢', label: '事件', size: 32 },
  'CONCEPT': { color: '#6C5CE7', icon: '💡', label: '概念', size: 32 },
  'default': { color: '#A29BFE', icon: '🔹', label: '实体', size: 30 }
};

/**
 * 获取实体配置
 */
const getEntityConfig = (type) => {
  return ENTITY_CONFIG[type] || ENTITY_CONFIG['default'];
};

/**
 * 融合版知识图谱组件
 */
const UnifiedKnowledgeGraph = () => {
  const svgRef = useRef(null);
  const graphContentRef = useRef(null);
  const simulationRef = useRef(null);
  const zoomRef = useRef(null);
  
  const { currentKnowledgeBase } = useKnowledgeStore();
  
  // 数据状态
  const [graphData, setGraphData] = useState({ entities: [], relationships: [] });
  const [filteredEntities, setFilteredEntities] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  
  // UI状态
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [selectedRelationship, setSelectedRelationship] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [entityTypeFilter, setEntityTypeFilter] = useState('all');
  
  // 构建状态
  const [buildingGraph, setBuildingGraph] = useState(false);
  const [buildProgress, setBuildProgress] = useState(0);
  const [buildStatus, setBuildStatus] = useState('');
  const [buildError, setBuildError] = useState(null);
  const [lastBuildTime, setLastBuildTime] = useState(null);
  const progressIntervalRef = useRef(null);

  /**
   * 获取图谱数据
   */
  const fetchGraphData = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    setLoading(true);
    setError('');
    
    try {
      const response = await getKnowledgeBaseGraphData(currentKnowledgeBase.id);
      
      // 转换后端数据为前端格式
      const entities = (response.nodes || response.entities || []).map((node, index) => ({
        id: node.id || node.entity_id || `entity-${index}`,
        name: node.name || node.label || node.text || `实体 ${index + 1}`,
        type: node.type || node.category || 'default',
        properties: node.properties || {},
        importance: node.importance || 0.5,
        x: Math.random() * 800,
        y: Math.random() * 600
      }));

      const relationships = (response.edges || response.relationships || response.links || []).map((edge, index) => ({
        id: edge.id || `rel-${index}`,
        source: edge.source || edge.source_id,
        target: edge.target || edge.target_id,
        relation: edge.label || edge.type || edge.relation || '关联',
        properties: edge.properties || {}
      }));

      const data = { entities, relationships };
      setGraphData(data);
      setFilteredEntities(entities);
      
      message.success({ content: '知识图谱加载成功' });
    } catch (error) {
      setError(error.message);
      message.error({ content: '获取知识图谱失败：' + error.message });
    } finally {
      setLoading(false);
    }
  }, [currentKnowledgeBase]);

  /**
   * 构建知识图谱
   */
  const handleBuildKnowledgeGraph = useCallback(async () => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    setBuildingGraph(true);
    setBuildStatus('extracting');
    setBuildProgress(0);
    setBuildError(null);

    try {
      const response = await buildKnowledgeGraph(null, currentKnowledgeBase.id);

      if (response.task_id) {
        startProgressPolling(response.task_id);
        message.success({ content: '知识图谱构建已启动' });
      } else {
        setBuildStatus('completed');
        setBuildProgress(100);
        setLastBuildTime(new Date());
        message.success({ content: '知识图谱构建完成' });
        fetchGraphData();
      }
    } catch (error) {
      setBuildStatus('failed');
      setBuildError(error.message);
      message.error({ content: '构建知识图谱失败：' + error.message });
    } finally {
      setBuildingGraph(false);
    }
  }, [currentKnowledgeBase, fetchGraphData]);

  /**
   * 进度轮询
   */
  const startProgressPolling = useCallback((taskId) => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }

    progressIntervalRef.current = setInterval(() => {
      setBuildProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressIntervalRef.current);
          setBuildStatus('completed');
          setLastBuildTime(new Date());
          fetchGraphData();
          return 100;
        }
        return prev + 5;
      });
    }, 1000);
  }, [fetchGraphData]);

  /**
   * 初始加载
   */
  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  /**
   * 清理
   */
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, []);

  /**
   * 搜索功能
   */
  useEffect(() => {
    if (!searchQuery) {
      setSearchResults([]);
      setFilteredEntities(graphData.entities);
      return;
    }

    const query = searchQuery.toLowerCase();
    const matched = graphData.entities.filter(entity => 
      entity.name.toLowerCase().includes(query) ||
      entity.type.toLowerCase().includes(query)
    );
    
    setSearchResults(matched);
    setFilteredEntities(matched);
  }, [searchQuery, graphData.entities]);

  /**
   * 实体类型筛选
   */
  useEffect(() => {
    if (entityTypeFilter === 'all') {
      setFilteredEntities(graphData.entities);
    } else {
      setFilteredEntities(graphData.entities.filter(e => e.type === entityTypeFilter));
    }
  }, [entityTypeFilter, graphData.entities]);

  /**
   * 渲染知识图谱
   */
  useEffect(() => {
    if (!svgRef.current || filteredEntities.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // 获取实际显示的关系（两个实体都在筛选后的列表中）
    const visibleEntityIds = new Set(filteredEntities.map(e => e.id));
    const visibleRelationships = graphData.relationships.filter(rel => 
      visibleEntityIds.has(typeof rel.source === 'object' ? rel.source.id : rel.source) &&
      visibleEntityIds.has(typeof rel.target === 'object' ? rel.target.id : rel.target)
    );

    // 创建力导向图模拟
    const simulation = d3.forceSimulation(filteredEntities)
      .force("link", d3.forceLink(visibleRelationships)
        .id(d => d.id)
        .distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(400, 300))
      .force("collision", d3.forceCollide().radius(50));

    simulationRef.current = simulation;

    // 创建缩放行为
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        graphContent.attr("transform", event.transform);
        setZoomLevel(event.transform.k);
      });

    zoomRef.current = zoom;
    svg.call(zoom);

    // 创建图形内容容器
    const graphContent = svg.append("g").attr("class", "graph-content");
    graphContentRef.current = graphContent;

    // 创建连线
    const link = graphContent.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(visibleRelationships)
      .enter().append("line")
      .attr("stroke", "#94a3b8")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 2)
      .on("click", (event, d) => {
        setSelectedRelationship(d);
        setSelectedEntity(null);
      });

    // 创建节点组
    const node = graphContent.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(filteredEntities)
      .enter().append("g")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // 节点圆圈
    node.append("circle")
      .attr("r", d => getEntityConfig(d.type).size * 0.4)
      .attr("fill", d => getEntityConfig(d.type).color)
      .attr("stroke", d => {
        const isHighlighted = searchResults.some(r => r.id === d.id);
        return isHighlighted ? "#ff6b6b" : "#fff";
      })
      .attr("stroke-width", d => {
        const isHighlighted = searchResults.some(r => r.id === d.id);
        return isHighlighted ? 3 : 2;
      })
      .on("click", (event, d) => {
        setSelectedEntity(d);
        setSelectedRelationship(null);
      });

    // 节点图标
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("font-size", "16px")
      .text(d => getEntityConfig(d.type).icon);

    // 节点标签
    node.append("text")
      .text(d => d.name)
      .attr("font-size", "12px")
      .attr("dy", d => getEntityConfig(d.type).size * 0.4 + 15)
      .attr("text-anchor", "middle")
      .attr("fill", "#334155")
      .attr("font-weight", "500");

    // 关系标签
    const linkText = graphContent.append("g")
      .attr("class", "link-labels")
      .selectAll("text")
      .data(visibleRelationships)
      .enter().append("text")
      .text(d => d.relation)
      .attr("font-size", "10px")
      .attr("fill", "#64748b")
      .attr("text-anchor", "middle");

    // 更新位置
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);

      linkText
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2);
    });

    // 拖拽函数
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [filteredEntities, graphData.relationships, searchResults]);

  /**
   * 缩放控制
   */
  const handleZoomIn = () => {
    if (svgRef.current && zoomRef.current) {
      d3.select(svgRef.current).transition().call(
        zoomRef.current.scaleBy, 1.2
      );
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current && zoomRef.current) {
      d3.select(svgRef.current).transition().call(
        zoomRef.current.scaleBy, 0.8
      );
    }
  };

  const handleZoomReset = () => {
    if (svgRef.current && zoomRef.current) {
      d3.select(svgRef.current).transition().call(
        zoomRef.current.transform, d3.zoomIdentity
      );
    }
  };

  /**
   * 导出图谱
   */
  const exportGraph = () => {
    if (!svgRef.current) return;
    
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `knowledge-graph-${currentKnowledgeBase?.name || 'export'}.svg`;
    link.click();
    URL.revokeObjectURL(url);
    
    message.success({ content: '图谱已导出' });
  };

  /**
   * 获取实体类型列表
   */
  const getEntityTypes = () => {
    const types = [...new Set(graphData.entities.map(e => e.type))];
    return types.map(type => ({
      type,
      ...getEntityConfig(type)
    }));
  };

  // 未选择知识库
  if (!currentKnowledgeBase) {
    return (
      <div className="knowledge-graph-empty">
        <div className="empty-icon">🕸️</div>
        <h3>请选择一个知识库</h3>
        <p>从左侧边栏选择一个知识库查看知识图谱</p>
      </div>
    );
  }

  // 加载中
  if (loading && graphData.entities.length === 0) {
    return (
      <div className="knowledge-graph-loading">
        <div className="loading-spinner"></div>
        <span>正在加载知识图谱...</span>
      </div>
    );
  }

  // 错误状态
  if (error && graphData.entities.length === 0) {
    return (
      <div className="knowledge-graph-error">
        <div className="error-icon">⚠️</div>
        <span>{error}</span>
        <button onClick={fetchGraphData} className="retry-btn">重试</button>
      </div>
    );
  }

  return (
    <div className="unified-knowledge-graph">
      {/* 工具栏 */}
      <div className="knowledge-graph-toolbar">
        <div className="toolbar-left">
          <h3>知识图谱</h3>
          <span className="graph-stats">
            {filteredEntities.length} 个实体 · {graphData.relationships.length} 个关系
          </span>
          {lastBuildTime && (
            <span className="last-build-time">
              上次构建: {lastBuildTime.toLocaleString('zh-CN')}
            </span>
          )}
        </div>

        <div className="toolbar-right">
          {/* 搜索框 */}
          <div className="search-box">
            <FiSearch size={16} />
            <input
              type="text"
              placeholder="搜索实体..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* 构建按钮 */}
          <Button
            variant="primary"
            size="sm"
            icon={<FiCpu />}
            onClick={handleBuildKnowledgeGraph}
            loading={buildingGraph}
            disabled={buildingGraph}
          >
            {buildingGraph ? '构建中...' : '构建知识图谱'}
          </Button>

          {/* 筛选按钮 */}
          <Button
            variant="ghost"
            size="sm"
            icon={<FiFilter />}
            onClick={() => setShowFilters(!showFilters)}
          >
            筛选
          </Button>

          {/* 缩放控制 */}
          <div className="zoom-controls">
            <button onClick={handleZoomOut} title="缩小">
              <FiZoomOut size={16} />
            </button>
            <span className="zoom-level">{Math.round(zoomLevel * 100)}%</span>
            <button onClick={handleZoomIn} title="放大">
              <FiZoomIn size={16} />
            </button>
            <button onClick={handleZoomReset} title="重置">
              <FiMaximize size={16} />
            </button>
          </div>

          {/* 刷新按钮 */}
          <Button
            variant="secondary"
            size="sm"
            icon={<FiRefreshCw />}
            onClick={fetchGraphData}
            loading={loading}
          >
            刷新
          </Button>

          {/* 导出按钮 */}
          <Button
            variant="ghost"
            size="sm"
            icon={<FiDownload />}
            onClick={exportGraph}
          >
            导出
          </Button>
        </div>
      </div>

      {/* 构建进度面板 */}
      {(buildingGraph || buildStatus === 'completed' || buildStatus === 'failed') && (
        <div className={`build-status-panel ${buildStatus}`}>
          <div className="build-status-header">
            {buildStatus === 'extracting' && <FiCpu className="status-icon" />}
            {buildStatus === 'building' && <div className="loading-spinner-small" />}
            {buildStatus === 'completed' && <FiCheckCircle className="status-icon" />}
            {buildStatus === 'failed' && <FiAlertCircle className="status-icon" />}
            <span className="status-text">
              {buildStatus === 'extracting' && '正在提取实体和关系...'}
              {buildStatus === 'building' && '正在构建知识图谱...'}
              {buildStatus === 'completed' && '知识图谱构建完成'}
              {buildStatus === 'failed' && '构建失败'}
            </span>
          </div>
          {buildingGraph && (
            <div className="build-progress">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${buildProgress}%` }} />
              </div>
              <span className="progress-text">{buildProgress}%</span>
            </div>
          )}
          {buildError && <div className="build-error">{buildError}</div>}
        </div>
      )}

      {/* 筛选面板 */}
      {showFilters && (
        <div className="filter-panel">
          <div className="filter-section">
            <label>实体类型</label>
            <select 
              value={entityTypeFilter} 
              onChange={(e) => setEntityTypeFilter(e.target.value)}
            >
              <option value="all">全部类型</option>
              {getEntityTypes().map(type => (
                <option key={type.type} value={type.type}>
                  {type.icon} {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* 主内容区 */}
      <div className="knowledge-graph-main">
        {/* 图谱可视化区 */}
        <div className="graph-visualization">
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            viewBox="0 0 800 600"
            preserveAspectRatio="xMidYMid meet"
            className="knowledge-graph-svg"
          />
          
          {loading && (
            <div className="graph-loading-overlay">
              <div className="loading-spinner" />
              <span>加载中...</span>
            </div>
          )}
        </div>

        {/* 详情面板 */}
        <div className="details-panel">
          {selectedEntity ? (
            <div className="entity-details">
              <div className="details-header">
                <h4>实体详情</h4>
                <button onClick={() => setSelectedEntity(null)}>×</button>
              </div>
              <div className="details-content">
                <div className="detail-item">
                  <span className="detail-label">名称</span>
                  <span className="detail-value">{selectedEntity.name}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">类型</span>
                  <span className="detail-value">
                    <span 
                      className="type-badge" 
                      style={{ background: getEntityConfig(selectedEntity.type).color }}
                    >
                      {getEntityConfig(selectedEntity.type).icon} {getEntityConfig(selectedEntity.type).label}
                    </span>
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">ID</span>
                  <span className="detail-value">{selectedEntity.id}</span>
                </div>
                {selectedEntity.importance && (
                  <div className="detail-item">
                    <span className="detail-label">重要性</span>
                    <span className="detail-value">{(selectedEntity.importance * 100).toFixed(0)}%</span>
                  </div>
                )}
              </div>
            </div>
          ) : selectedRelationship ? (
            <div className="relationship-details">
              <div className="details-header">
                <h4>关系详情</h4>
                <button onClick={() => setSelectedRelationship(null)}>×</button>
              </div>
              <div className="details-content">
                <div className="detail-item">
                  <span className="detail-label">关系类型</span>
                  <span className="detail-value">{selectedRelationship.relation}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">源实体</span>
                  <span className="detail-value">
                    {typeof selectedRelationship.source === 'object' 
                      ? selectedRelationship.source.name 
                      : selectedRelationship.source}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">目标实体</span>
                  <span className="detail-value">
                    {typeof selectedRelationship.target === 'object' 
                      ? selectedRelationship.target.name 
                      : selectedRelationship.target}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="details-empty">
              <p>点击节点或连线查看详情</p>
            </div>
          )}

          {/* 图例 */}
          <div className="graph-legend">
            <h4>图例</h4>
            {getEntityTypes().map(type => (
              <div key={type.type} className="legend-item">
                <span 
                  className="legend-color" 
                  style={{ background: type.color }}
                />
                <span className="legend-icon">{type.icon}</span>
                <span className="legend-label">{type.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedKnowledgeGraph;
