/**
 * 文档图谱组件
 *
 * 使用 D3.js 力导向图可视化文档级别的实体关系图谱
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FiZoomIn, FiZoomOut, FiRotateCcw, FiDownload, FiSettings } from 'react-icons/fi';
import * as d3 from 'd3';
import { getDocumentGraph } from '../../utils/api/hierarchyApi';
import './DocumentGraph.css';

/**
 * 实体类型颜色配置
 */
const ENTITY_TYPE_COLORS = {
  'PERSON': '#FF6B6B',      // 红色 - 人物
  'ORG': '#4ECDC4',         // 青色 - 组织
  'ORGANIZATION': '#4ECDC4', // 青色 - 组织
  'LOC': '#45B7D1',         // 蓝色 - 地点
  'LOCATION': '#45B7D1',    // 蓝色 - 地点
  'EVENT': '#FDCB6E',       // 黄色 - 事件
  'CONCEPT': '#6C5CE7',     // 紫色 - 概念
  'PRODUCT': '#FD79A8',     // 粉色 - 产品
  'TECH': '#A29BFE',        // 淡紫色 - 技术
  'DATE': '#96CEB4',        // 绿色 - 日期
  'MONEY': '#FECA57',       // 金黄色 - 金额
  'default': '#A29BFE'      // 默认颜色
};

/**
 * 获取实体类型的颜色
 * @param {string} type - 实体类型
 * @returns {string} 颜色值
 */
const getEntityColor = (type) => {
  return ENTITY_TYPE_COLORS[type?.toUpperCase()] || ENTITY_TYPE_COLORS['default'];
};

/**
 * 获取实体类型的显示名称
 * @param {string} type - 实体类型
 * @returns {string} 显示名称
 */
const getEntityTypeLabel = (type) => {
  const labels = {
    'PERSON': '人物',
    'ORG': '组织',
    'ORGANIZATION': '组织',
    'LOC': '地点',
    'LOCATION': '地点',
    'EVENT': '事件',
    'CONCEPT': '概念',
    'PRODUCT': '产品',
    'TECH': '技术',
    'DATE': '日期',
    'MONEY': '金额'
  };
  return labels[type?.toUpperCase()] || type || '未知';
};

const DocumentGraph = ({ knowledgeBaseId, documentId }) => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    nodeSize: 20,
    linkWidth: 2,
    showLabels: true,
    showLinkLabels: true,
    chargeStrength: -300,
    linkDistance: 100
  });

  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const simulationRef = useRef(null);
  const gRef = useRef(null);

  // 加载图谱数据
  useEffect(() => {
    if (knowledgeBaseId && documentId) {
      loadGraphData();
    }
  }, [knowledgeBaseId, documentId]);

  /**
   * 加载文档图谱数据
   */
  const loadGraphData = async () => {
    setLoading(true);
    setError(null);
    try {
      const docId = typeof documentId === 'object' ? documentId.id || documentId.document_id : documentId;
      console.log('[DocumentGraph] 加载图谱数据:', { knowledgeBaseId, documentId: docId });
      const response = await getDocumentGraph(knowledgeBaseId, docId);

      // 处理数据格式
      const nodes = response.nodes || response.entities || [];
      const links = response.links || response.relationships || response.edges || [];

      console.log('[DocumentGraph] 图谱数据:', { nodes: nodes.length, links: links.length });

      setGraphData({ nodes, links });
    } catch (err) {
      console.error('加载文档图谱失败:', err);
      setError('加载图谱失败，请稍后重试');
      setGraphData({ nodes: [], links: [] });
    } finally {
      setLoading(false);
    }
  };

  /**
   * 渲染力导向图
   */
  const renderForceGraph = useCallback(() => {
    if (!svgRef.current || !containerRef.current || graphData.nodes.length === 0) {
      return;
    }

    const svg = d3.select(svgRef.current);
    const container = d3.select(containerRef.current);

    // 清空之前的内容
    svg.selectAll('*').remove();

    // 获取容器尺寸
    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 600;

    // 设置SVG尺寸
    svg.attr('width', width).attr('height', height);

    // 创建缩放行为
    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    // 应用缩放到SVG
    svg.call(zoom);

    // 创建主组
    const g = svg.append('g');
    gRef.current = g;

    // 预处理节点数据
    const nodes = graphData.nodes.map((node, index) => ({
      ...node,
      id: node.id || node.entity_id || `node_${index}`,
      name: node.name || node.label || node.text || `实体${index}`,
      type: node.type || node.category || 'default'
    }));

    // 创建节点ID映射
    const nodeMap = {};
    nodes.forEach(node => {
      nodeMap[node.id] = node;
    });

    // 预处理连接数据
    const links = graphData.links.map((link, index) => {
      let source = link.source;
      let target = link.target;

      // 处理source和target可能是ID字符串的情况
      if (typeof source === 'string' || typeof source === 'number') {
        source = nodeMap[source] || null;
      }
      if (typeof target === 'string' || typeof target === 'number') {
        target = nodeMap[target] || null;
      }

      return {
        ...link,
        source,
        target,
        relation: link.relation || link.label || link.type || '相关'
      };
    }).filter(link => link.source && link.target);

    console.log('[DocumentGraph] 处理后的数据:', { nodes: nodes.length, links: links.length });

    // 创建力导向模拟
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(settings.linkDistance))
      .force('charge', d3.forceManyBody().strength(settings.chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(settings.nodeSize + 10));

    simulationRef.current = simulation;

    // 绘制连接线
    const linkGroup = g.append('g').attr('class', 'links');

    const link = linkGroup.selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', settings.linkWidth)
      .attr('stroke-opacity', 0.6);

    // 绘制连接线标签
    let linkText;
    if (settings.showLinkLabels) {
      linkText = linkGroup.selectAll('.link-label')
        .data(links)
        .enter().append('text')
        .attr('class', 'link-label')
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#64748b')
        .attr('dy', -3)
        .text(d => d.relation);
    }

    // 绘制节点
    const nodeGroup = g.append('g').attr('class', 'nodes');

    const node = nodeGroup.selectAll('.node')
      .data(nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // 节点圆圈 - 使用实体类型对应的颜色
    node.append('circle')
      .attr('r', settings.nodeSize)
      .attr('fill', d => getEntityColor(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer');

    // 节点标签
    if (settings.showLabels) {
      node.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', settings.nodeSize + 15)
        .attr('font-size', '12px')
        .attr('fill', '#333')
        .attr('font-weight', '500')
        .text(d => d.name);
    }

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);

      if (settings.showLinkLabels && linkText) {
        linkText
          .attr('x', d => (d.source.x + d.target.x) / 2)
          .attr('y', d => (d.source.y + d.target.y) / 2);
      }
    });

    // 组件卸载时停止模拟
    return () => {
      simulation.stop();
    };
  }, [graphData, settings]);

  // 渲染图谱
  useEffect(() => {
    const cleanup = renderForceGraph();
    return () => {
      if (cleanup) cleanup();
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, [renderForceGraph]);

  /**
   * 处理缩放 - 使用D3 zoom行为
   */
  const handleZoom = (direction) => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const currentTransform = d3.zoomTransform(svgRef.current);
    let newScale = currentTransform.k;

    if (direction === 'in' && newScale < 3) {
      newScale += 0.2;
    } else if (direction === 'out' && newScale > 0.5) {
      newScale -= 0.2;
    }

    // 获取SVG中心点
    const width = svgRef.current.clientWidth || 800;
    const height = svgRef.current.clientHeight || 600;

    // 以中心点进行缩放
    svg.transition()
      .duration(300)
      .call(
        d3.zoom().transform,
        d3.zoomIdentity.translate(width / 2, height / 2).scale(newScale).translate(-width / 2, -height / 2)
      );

    setZoomLevel(newScale);
  };

  /**
   * 重置视图
   */
  const handleReset = () => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);

    // 重置变换
    svg.transition()
      .duration(300)
      .call(d3.zoom().transform, d3.zoomIdentity);

    setZoomLevel(1);

    // 重新启动力导向模拟
    if (simulationRef.current) {
      simulationRef.current.alpha(1).restart();
    }
  };

  /**
   * 下载图谱
   */
  const handleDownload = () => {
    if (!svgRef.current) return;

    const svg = svgRef.current;
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svg);
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `document-graph-${documentId}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  /**
   * 处理设置更改
   */
  const handleSettingChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  /**
   * 获取实际存在的实体类型
   */
  const getExistingEntityTypes = () => {
    const types = new Set();
    graphData.nodes.forEach(node => {
      if (node.type) {
        types.add(node.type.toUpperCase());
      }
    });
    return Array.from(types);
  };

  return (
    <div className="document-graph">
      <div className="dg-header">
        <h3>文档关系图谱</h3>
        <div className="dg-controls">
          <button
            className="control-btn"
            onClick={() => handleZoom('out')}
            title="缩小"
          >
            <FiZoomOut />
          </button>
          <button
            className="control-btn"
            onClick={handleReset}
            title="重置"
          >
            <FiRotateCcw />
          </button>
          <button
            className="control-btn"
            onClick={() => handleZoom('in')}
            title="放大"
          >
            <FiZoomIn />
          </button>
          <button
            className="control-btn"
            onClick={handleDownload}
            title="下载"
          >
            <FiDownload />
          </button>
          <button
            className="control-btn"
            onClick={() => setShowSettings(!showSettings)}
            title="设置"
          >
            <FiSettings />
          </button>
        </div>
      </div>

      {/* 设置面板 */}
      {showSettings && (
        <div className="settings-panel">
          <h4>图谱设置</h4>
          <div className="setting-item">
            <label>节点大小:</label>
            <input
              type="range"
              min="10"
              max="40"
              value={settings.nodeSize}
              onChange={(e) => handleSettingChange('nodeSize', parseInt(e.target.value))}
            />
            <span>{settings.nodeSize}</span>
          </div>
          <div className="setting-item">
            <label>连接线宽度:</label>
            <input
              type="range"
              min="1"
              max="5"
              step="0.5"
              value={settings.linkWidth}
              onChange={(e) => handleSettingChange('linkWidth', parseFloat(e.target.value))}
            />
            <span>{settings.linkWidth}</span>
          </div>
          <div className="setting-item">
            <label>节点斥力:</label>
            <input
              type="range"
              min="-500"
              max="-100"
              step="50"
              value={settings.chargeStrength}
              onChange={(e) => handleSettingChange('chargeStrength', parseInt(e.target.value))}
            />
            <span>{settings.chargeStrength}</span>
          </div>
          <div className="setting-item">
            <label>连接距离:</label>
            <input
              type="range"
              min="50"
              max="200"
              step="10"
              value={settings.linkDistance}
              onChange={(e) => handleSettingChange('linkDistance', parseInt(e.target.value))}
            />
            <span>{settings.linkDistance}</span>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.showLabels}
                onChange={(e) => handleSettingChange('showLabels', e.target.checked)}
              />
              显示节点标签
            </label>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.showLinkLabels}
                onChange={(e) => handleSettingChange('showLinkLabels', e.target.checked)}
              />
              显示关系标签
            </label>
          </div>
        </div>
      )}

      {/* 图谱内容 */}
      <div className="dg-content" ref={containerRef}>
        {loading ? (
          <div className="loading">加载中...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : graphData.nodes.length === 0 ? (
          <div className="empty">暂无图谱数据</div>
        ) : (
          <>
            <svg ref={svgRef} className="graph-svg"></svg>
            <div className="graph-info">
              节点: {graphData.nodes.length} | 连接: {graphData.links.length} | 缩放: {(zoomLevel * 100).toFixed(0)}%
            </div>
            <div className="graph-hint">
              滚轮缩放 | 拖拽平移 | 拖拽节点调整位置
            </div>
          </>
        )}
      </div>

      {/* 图例 - 显示实际数据中存在的实体类型 */}
      {graphData.nodes.length > 0 && (
        <div className="graph-legend">
          <h4>图例</h4>
          <div className="legend-items">
            {getExistingEntityTypes().map((type, index) => (
              <div key={`dg-legend-${type}-${index}`} className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: getEntityColor(type) }}
                ></div>
                <span>{getEntityTypeLabel(type)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentGraph;
