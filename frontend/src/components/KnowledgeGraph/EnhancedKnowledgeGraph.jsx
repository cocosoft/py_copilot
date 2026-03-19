/**
 * 增强版知识图谱组件
 * 
 * 基于D3.js实现的高级知识图谱可视化和分析功能
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { FiRefreshCw, FiZoomIn, FiZoomOut, FiMaximize, FiFilter, FiCpu, FiCheckCircle, FiAlertCircle, FiSearch, FiDownload, FiShare2, FiInfo } from 'react-icons/fi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import { Button } from '../UI';
import { message } from '../UI/Message/Message';
import {
  getKnowledgeBaseGraphData,
  buildKnowledgeGraph
} from '../../utils/api/knowledgeApi';
import './EnhancedKnowledgeGraph.css';

// 动态导入D3.js，减少初始加载时间
const loadD3 = async () => {
  if (window.d3) {
    return window.d3;
  }
  const d3 = await import('d3');
  window.d3 = d3.default;
  return d3.default;
};

/**
 * 增强版知识图谱组件
 */
const EnhancedKnowledgeGraph = ({ knowledgeBaseId, onNodeClick, className }) => {
  const svgRef = useRef(null);
  const { currentKnowledgeBase } = useKnowledgeStore();
  
  // 本地状态
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredNodes, setFilteredNodes] = useState([]);
  const [forceSimulation, setForceSimulation] = useState(null);
  const [zoomTransform, setZoomTransform] = useState({ k: 1, x: 0, y: 0 });
  
  // 知识图谱构建状态
  const [buildingGraph, setBuildingGraph] = useState(false);
  const [buildProgress, setBuildProgress] = useState(0);
  const [buildStatus, setBuildStatus] = useState('');
  const [buildError, setBuildError] = useState(null);
  const [lastBuildTime, setLastBuildTime] = useState(null);
  const progressIntervalRef = useRef(null);
  
  // D3相关引用
  const d3Ref = useRef(null);
  const simulationRef = useRef(null);
  const zoomRef = useRef(null);
  const linkElementsRef = useRef(null);
  const nodeElementsRef = useRef(null);
  
  /**
   * 获取图谱数据
   */
  const fetchGraphData = useCallback(async () => {
    const kbId = knowledgeBaseId || currentKnowledgeBase?.id;
    if (!kbId) return;

    setLoading(true);
    try {
      // 调用真实 API 获取知识图谱数据
      const response = await getKnowledgeBaseGraphData(kbId);

      // 转换后端数据为前端格式
      const nodes = (response.nodes || []).map((node, index) => ({
        id: node.id || `node-${index}`,
        label: node.name || node.label || `实体 ${index + 1}`,
        type: node.type || 'entity',
        importance: node.importance || 0.5,
        properties: node.properties || {},
        relatedDocuments: node.related_documents || []
      }));

      const edges = (response.edges || response.relationships || []).map((edge, index) => ({
        id: edge.id || `edge-${index}`,
        source: edge.source || edge.source_id,
        target: edge.target || edge.target_id,
        label: edge.label || edge.type || '关联',
        strength: edge.strength || 1,
        properties: edge.properties || {}
      }));

      setGraphData({ nodes, edges });
      setFilteredNodes(nodes);
    } catch (error) {
      message.error({ content: '获取知识图谱失败：' + error.message });
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, currentKnowledgeBase]);

  // 初始加载
  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  // 清理进度轮询
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
   * 构建知识图谱
   */
  const handleBuildKnowledgeGraph = useCallback(async () => {
    const kbId = knowledgeBaseId || currentKnowledgeBase?.id;
    if (!kbId) return;

    setBuildingGraph(true);
    setBuildStatus('extracting');
    setBuildProgress(0);
    setBuildError(null);

    try {
      // 启动知识图谱构建
      const response = await buildKnowledgeGraph(null, kbId);

      if (response.task_id) {
        // 开始轮询进度
        startProgressPolling(response.task_id);
        message.success({ content: '知识图谱构建已启动' });
      } else {
        // 同步完成
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
  }, [knowledgeBaseId, currentKnowledgeBase, fetchGraphData]);

  /**
   * 开始进度轮询
   */
  const startProgressPolling = useCallback((taskId) => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }

    progressIntervalRef.current = setInterval(async () => {
      try {
        // 这里应该调用获取任务进度的 API
        // 暂时模拟进度增长
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
      } catch (error) {
        console.error('获取进度失败:', error);
      }
    }, 1000);
  }, [fetchGraphData]);

  /**
   * 绘制知识图谱
   */
  useEffect(() => {
    const drawGraph = async () => {
      if (!svgRef.current || graphData.nodes.length === 0) return;

      const d3 = await loadD3();
      d3Ref.current = d3;

      // 清除旧的内容
      const svg = d3.select(svgRef.current);
      svg.selectAll('*').remove();

      // 设置画布尺寸
      const width = svgRef.current.clientWidth;
      const height = svgRef.current.clientHeight;

      // 创建缩放行为
      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
          setZoomTransform(event.transform);
        });

      zoomRef.current = zoom;
      svg.call(zoom);

      // 创建容器组
      const g = svg.append('g');

      // 创建力导向模拟
      const simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.edges).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => (d.importance || 0.5) * 30 + 10));

      simulationRef.current = simulation;
      setForceSimulation(simulation);

      // 绘制边
      const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(graphData.edges)
        .enter().append('line')
        .attr('stroke', '#d9d9d9')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.strength || 1));

      linkElementsRef.current = link;

      // 边标签
      const linkLabel = g.append('g')
        .attr('class', 'link-labels')
        .selectAll('text')
        .data(graphData.edges)
        .enter().append('text')
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#666')
        .text(d => d.label);

      // 绘制节点
      const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(graphData.nodes)
        .enter().append('g')
        .attr('class', 'node')
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended));

      nodeElementsRef.current = node;

      // 节点圆形
      node.append('circle')
        .attr('r', d => (d.importance || 0.5) * 30)
        .attr('fill', d => {
          const colors = {
            concept: '#1890ff',
            entity: '#52c41a',
            relation: '#faad14',
            event: '#ff4d4f',
            location: '#722ed1',
            organization: '#fa8c16',
            person: '#13c2c2'
          };
          return colors[d.type] || '#8c8c8c';
        })
        .attr('stroke', d => selectedNode?.id === d.id ? '#1890ff' : 'none')
        .attr('stroke-width', d => selectedNode?.id === d.id ? 3 : 0)
        .on('click', (event, d) => {
          setSelectedNode(d);
          if (onNodeClick) {
            onNodeClick(d);
          }
        });

      // 节点标签
      node.append('text')
        .attr('dy', 4)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .attr('fill', '#262626')
        .text(d => d.label)
        .call(wrapText, 100);

      // 力导向模拟更新
      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        linkLabel
          .attr('x', d => (d.source.x + d.target.x) / 2)
          .attr('y', d => (d.source.y + d.target.y) / 2);

        node
          .attr('transform', d => `translate(${d.x},${d.y})`);
      });

      // 拖拽函数
      function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }

      function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }

      function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }

      // 文本换行函数
      function wrapText(text, width) {
        text.each(function() {
          const text = d3.select(this);
          const words = text.text().split(/\s+/).reverse();
          let word;
          let line = [];
          let lineNumber = 0;
          const lineHeight = 1.2;
          const y = text.attr('y');
          const dy = parseFloat(text.attr('dy'));
          let tspan = text.text(null).append('tspan')
            .attr('x', 0)
            .attr('y', y)
            .attr('dy', dy + 'em');

          while (word = words.pop()) {
            line.push(word);
            tspan.text(line.join(' '));
            if (tspan.node().getComputedTextLength() > width) {
              line.pop();
              tspan.text(line.join(' '));
              line = [word];
              tspan = text.append('tspan')
                .attr('x', 0)
                .attr('y', y)
                .attr('dy', ++lineNumber * lineHeight + dy + 'em')
                .text(word);
            }
          }
        });
      }
    };

    drawGraph();
  }, [graphData, selectedNode, onNodeClick]);

  /**
   * 搜索节点
   */
  const handleSearch = useCallback(() => {
    if (!searchQuery.trim()) {
      setFilteredNodes(graphData.nodes);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = graphData.nodes.filter(node => 
      node.label.toLowerCase().includes(query) ||
      (node.properties && Object.values(node.properties).some(value => 
        String(value).toLowerCase().includes(query)
      ))
    );

    setFilteredNodes(filtered);
    
    // 高亮搜索结果
    if (d3Ref.current && nodeElementsRef.current) {
      nodeElementsRef.current
        .select('circle')
        .attr('stroke', d => filtered.some(n => n.id === d.id) ? '#ff4d4f' : (selectedNode?.id === d.id ? '#1890ff' : 'none'))
        .attr('stroke-width', d => filtered.some(n => n.id === d.id) ? 3 : (selectedNode?.id === d.id ? 3 : 0));
    }
  }, [searchQuery, graphData, selectedNode]);

  /**
   * 导出知识图谱
   */
  const handleExport = useCallback(() => {
    if (graphData.nodes.length === 0) {
      message.warning({ content: '没有数据可导出' });
      return;
    }

    // 导出为JSON
    const exportData = {
      nodes: graphData.nodes,
      edges: graphData.edges,
      exportTime: new Date().toISOString(),
      knowledgeBase: currentKnowledgeBase?.name || 'Unknown'
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge-graph-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    message.success({ content: '知识图谱导出成功' });
  }, [graphData, currentKnowledgeBase]);

  /**
   * 缩放操作
   */
  const handleZoomIn = useCallback(() => {
    if (zoomRef.current && svgRef.current) {
      const svg = d3Ref.current.select(svgRef.current);
      svg.transition().call(zoomRef.current.scaleBy, 1.2);
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (zoomRef.current && svgRef.current) {
      const svg = d3Ref.current.select(svgRef.current);
      svg.transition().call(zoomRef.current.scaleBy, 0.8);
    }
  }, []);

  const handleReset = useCallback(() => {
    if (zoomRef.current && svgRef.current) {
      const svg = d3Ref.current.select(svgRef.current);
      svg.transition().call(zoomRef.current.transform, d3Ref.current.zoomIdentity);
    }
  }, []);

  const kbId = knowledgeBaseId || currentKnowledgeBase?.id;
  if (!kbId) {
    return (
      <div className={`enhanced-knowledge-graph ${className || ''}`}>
        <div className="knowledge-graph-empty">
          <div className="empty-icon">🕸️</div>
          <h3>请选择一个知识库</h3>
          <p>从左侧边栏选择一个知识库查看知识图谱</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`enhanced-knowledge-graph ${className || ''}`}>
      {/* 工具栏 */}
      <div className="knowledge-graph-toolbar">
        <div className="toolbar-left">
          <h3>增强版知识图谱</h3>
          <span className="graph-stats">
            {graphData.nodes.length} 个实体 · {graphData.edges.length} 个关系
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
            <input
              type="text"
              placeholder="搜索实体..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button onClick={handleSearch} title="搜索">
              <FiSearch size={16} />
            </button>
          </div>

          {/* 构建知识图谱按钮 */}
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

          <Button
            variant="ghost"
            size="sm"
            icon={<FiFilter />}
          >
            筛选
          </Button>

          <div className="zoom-controls">
            <button onClick={handleZoomOut} title="缩小">
              <FiZoomOut size={16} />
            </button>
            <span className="zoom-level">{Math.round(zoomTransform.k * 100)}%</span>
            <button onClick={handleZoomIn} title="放大">
              <FiZoomIn size={16} />
            </button>
            <button onClick={handleReset} title="重置">
              <FiMaximize size={16} />
            </button>
          </div>

          <Button
            variant="secondary"
            size="sm"
            icon={<FiRefreshCw />}
            onClick={fetchGraphData}
            loading={loading}
          >
            刷新
          </Button>

          <Button
            variant="ghost"
            size="sm"
            icon={<FiDownload />}
            onClick={handleExport}
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
            {buildStatus === 'building' && <FiPlay className="status-icon" />}
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
                <div
                  className="progress-fill"
                  style={{ width: `${buildProgress}%` }}
                />
              </div>
              <span className="progress-text">{buildProgress}%</span>
            </div>
          )}
          {buildError && (
            <div className="build-error">{buildError}</div>
          )}
        </div>
      )}

      {/* 主内容区 */}
      <div className="knowledge-graph-content">
        {/* 图谱画布 */}
        <div className="graph-canvas-wrapper">
          <svg
            ref={svgRef}
            className="graph-svg"
          />
          
          {loading && (
            <div className="graph-loading">
              <div className="loading-spinner" />
              <span>加载图谱中...</span>
            </div>
          )}

          {graphData.nodes.length === 0 && !loading && (
            <div className="graph-empty">
              <div className="empty-icon">🔍</div>
              <h4>暂无知识图谱数据</h4>
              <p>点击"构建知识图谱"按钮开始构建</p>
            </div>
          )}
        </div>

        {/* 节点详情面板 */}
        {selectedNode && (
          <div className="node-detail-panel">
            <div className="node-detail-header">
              <h4>节点详情</h4>
              <button 
                className="close-detail"
                onClick={() => setSelectedNode(null)}
              >
                ×
              </button>
            </div>
            <div className="node-detail-content">
              <div className="detail-item">
                <label>ID</label>
                <span>{selectedNode.id}</span>
              </div>
              <div className="detail-item">
                <label>名称</label>
                <span>{selectedNode.label}</span>
              </div>
              <div className="detail-item">
                <label>类型</label>
                <span className={`type-badge ${selectedNode.type}`}>
                  {selectedNode.type === 'concept' && '概念'}
                  {selectedNode.type === 'entity' && '实体'}
                  {selectedNode.type === 'relation' && '关系'}
                  {selectedNode.type === 'event' && '事件'}
                  {selectedNode.type === 'location' && '地点'}
                  {selectedNode.type === 'organization' && '组织'}
                  {selectedNode.type === 'person' && '人物'}
                  {!['concept', 'entity', 'relation', 'event', 'location', 'organization', 'person'].includes(selectedNode.type) && selectedNode.type}
                </span>
              </div>
              <div className="detail-item">
                <label>重要性</label>
                <span>{(selectedNode.importance || 0.5).toFixed(2)}</span>
              </div>
              <div className="detail-item">
                <label>关联数</label>
                <span>
                  {graphData.edges.filter(e => 
                    e.source === selectedNode.id || e.target === selectedNode.id
                  ).length}
                </span>
              </div>
              
              {/* 相关文档 */}
              {selectedNode.relatedDocuments && selectedNode.relatedDocuments.length > 0 && (
                <div className="detail-section">
                  <h5>相关文档</h5>
                  <ul className="related-documents">
                    {selectedNode.relatedDocuments.slice(0, 5).map((doc, index) => (
                      <li key={index}>
                        <FiInfo size={14} />
                        <span>{doc.title || doc.name || `文档 ${index + 1}`}</span>
                      </li>
                    ))}
                    {selectedNode.relatedDocuments.length > 5 && (
                      <li className="more-docs">
                        还有 {selectedNode.relatedDocuments.length - 5} 个相关文档
                      </li>
                    )}
                  </ul>
                </div>
              )}
              
              {/* 节点属性 */}
              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div className="detail-section">
                  <h5>属性</h5>
                  <div className="node-properties">
                    {Object.entries(selectedNode.properties).map(([key, value]) => (
                      <div key={key} className="property-item">
                        <span className="property-key">{key}</span>
                        <span className="property-value">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedKnowledgeGraph;