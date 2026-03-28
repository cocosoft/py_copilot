/**
 * 知识库知识图谱组件
 *
 * 用于可视化知识库级别的实体关系图谱
 * 使用 D3.js 力导向图和真实数据
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FiZoomIn, FiZoomOut, FiRotateCcw, FiDownload, FiSettings } from 'react-icons/fi';
import * as d3 from 'd3';
import useKnowledgeStore from '../../stores/knowledgeStore';
import { getKnowledgeBaseGraph } from '../../utils/api/hierarchyApi';
import './KBGraph.css';

const KBGraph = ({ knowledgeBaseId }) => {
  const { setHierarchyLevel, setCurrentEntity } = useKnowledgeStore();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    nodeSize: 20,
    linkWidth: 1.5,
    showLabels: true,
    chargeStrength: -300,
    linkDistance: 100
  });

  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const simulationRef = useRef(null);
  const zoomRef = useRef(null);

  /**
   * 实体类型颜色映射
   */
  const getEntityColor = useCallback((type) => {
    const colorMap = {
      'CONCEPT': '#1890ff',
      'PERSON': '#ff6b6b',
      'ORGANIZATION': '#4ecdc4',
      'LOCATION': '#45b7d1',
      'DATE': '#96ceb4',
      'MONEY': '#feca57',
      'TECH': '#a29bfe',
      'PRODUCT': '#fd79a8',
      'EVENT': '#fdcb6e',
      '概念': '#1890ff',
      '人物': '#ff6b6b',
      '组织': '#4ecdc4',
      '地点': '#45b7d1',
      '日期': '#96ceb4',
      '金额': '#feca57',
      '技术': '#a29bfe',
      '产品': '#fd79a8',
      '事件': '#fdcb6e'
    };
    return colorMap[type?.toUpperCase()] || '#666666';
  }, []);

  /**
   * 加载知识库图谱数据
   */
  const loadGraphData = useCallback(async () => {
    if (!knowledgeBaseId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await getKnowledgeBaseGraph(knowledgeBaseId);

      if (response.code === 200 && response.data) {
        const data = response.data;
        const nodes = data.nodes || [];
        const links = data.edges || data.links || [];

        // 转换数据格式
        const formattedNodes = nodes.map(node => ({
          id: node.id || node.entity_id,
          name: node.name || node.text || node.label || `实体${node.id}`,
          type: node.type || node.entity_type || '未知',
          ...node
        }));

        const formattedLinks = links.map(link => ({
          source: link.source?.id || link.source_id || link.source,
          target: link.target?.id || link.target_id || link.target,
          label: link.label || link.relationship_type || link.type || '',
          value: link.value || link.confidence || 1,
          ...link
        }));

        setGraphData({
          nodes: formattedNodes,
          links: formattedLinks
        });
      } else {
        setError(response.message || '加载图谱数据失败');
      }
    } catch (err) {
      console.error('加载知识库图谱失败:', err);
      setError('加载图谱失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId]);

  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  /**
   * 渲染 D3 力导向图
   */
  useEffect(() => {
    if (!svgRef.current || graphData.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth || 800;
    const height = svgRef.current.clientHeight || 600;

    // 创建主容器组
    const g = svg.append('g');

    // 创建缩放行为
    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoomLevel(event.transform.k);
      });

    zoomRef.current = zoom;
    svg.call(zoom);

    // 创建力导向模拟
    const simulation = d3.forceSimulation(graphData.nodes)
      .force('link', d3.forceLink(graphData.links)
        .id(d => d.id)
        .distance(settings.linkDistance)
      )
      .force('charge', d3.forceManyBody().strength(settings.chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => Math.max(settings.nodeSize, (d.count || 1) * 0.3) + 5));

    simulationRef.current = simulation;

    // 绘制连线
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(graphData.links)
      .enter()
      .append('line')
      .attr('stroke', '#999999')
      .attr('stroke-width', settings.linkWidth)
      .attr('stroke-opacity', 0.6);

    // 绘制连线标签
    const linkLabel = g.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(graphData.links)
      .enter()
      .append('text')
      .attr('font-size', '10px')
      .attr('fill', '#666666')
      .attr('text-anchor', 'middle')
      .text(d => d.label || '');

    // 绘制节点
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(graphData.nodes)
      .enter()
      .append('circle')
      .attr('r', d => Math.max(settings.nodeSize, (d.count || 1) * 0.3))
      .attr('fill', d => getEntityColor(d.type))
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
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

    // 绘制节点标签
    const nodeLabel = settings.showLabels ? g.append('g')
      .attr('class', 'node-labels')
      .selectAll('text')
      .data(graphData.nodes)
      .enter()
      .append('text')
      .attr('font-size', '12px')
      .attr('fill', '#333333')
      .attr('text-anchor', 'middle')
      .attr('dy', d => Math.max(settings.nodeSize, (d.count || 1) * 0.3) + 15)
      .text(d => d.name || d.text || '') : null;

    // 节点双击事件
    node.on('dblclick', (event, d) => {
      event.stopPropagation();
      setCurrentEntity(d);
      setHierarchyLevel('document');
    });

    // 节点悬停提示
    node.append('title')
      .text(d => `${d.name || d.text || '未知'} (${d.type || '未知类型'})`);

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      linkLabel
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2 - 5);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      if (nodeLabel) {
        nodeLabel
          .attr('x', d => d.x)
          .attr('y', d => d.y);
      }
    });

    // 组件卸载时停止模拟
    return () => {
      simulation.stop();
    };
  }, [graphData, settings, getEntityColor, setCurrentEntity, setHierarchyLevel]);

  /**
   * 处理缩放 - 使用D3 zoom行为
   */
  const handleZoom = (direction) => {
    if (!svgRef.current || !zoomRef.current) return;

    const svg = d3.select(svgRef.current);
    const currentTransform = d3.zoomTransform(svgRef.current);
    let newScale = currentTransform.k;

    if (direction === 'in' && newScale < 3) {
      newScale += 0.2;
    } else if (direction === 'out' && newScale > 0.5) {
      newScale -= 0.2;
    }

    const width = svgRef.current.clientWidth || 800;
    const height = svgRef.current.clientHeight || 600;

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
    if (!svgRef.current || !zoomRef.current) return;

    const svg = d3.select(svgRef.current);

    svg.transition()
      .duration(300)
      .call(d3.zoom().transform, d3.zoomIdentity);

    setZoomLevel(1);

    if (simulationRef.current) {
      simulationRef.current.alpha(1).restart();
    }
  };

  /**
   * 下载图谱数据
   */
  const handleDownload = () => {
    const data = JSON.stringify(graphData, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kb-graph-${knowledgeBaseId}.json`;
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

  /**
   * 渲染图例 - 只显示实际存在的类型
   */
  const renderLegend = () => {
    const existingTypes = getExistingEntityTypes();

    if (existingTypes.length === 0) return null;

    const typeLabels = {
      'CONCEPT': '概念',
      'PERSON': '人物',
      'ORGANIZATION': '组织',
      'LOCATION': '地点',
      'DATE': '日期',
      'MONEY': '金额',
      'TECH': '技术',
      'PRODUCT': '产品',
      'EVENT': '事件'
    };

    return (
      <div className="graph-legend">
        <h4>图例</h4>
        <div className="legend-items">
          {existingTypes.map((type, index) => (
            <div key={`kb-legend-${type}-${index}`} className="legend-item">
              <div
                className="legend-color"
                style={{ backgroundColor: getEntityColor(type) }}
              ></div>
              <span className="legend-label">{typeLabels[type] || type}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="kb-graph">
      <div className="kb-graph-header">
        <h3>知识库知识图谱</h3>
        <div className="graph-controls">
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
              显示标签
            </label>
          </div>
        </div>
      )}

      {/* 图谱内容 */}
      <div className="kb-graph-content" ref={containerRef}>
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
              滚轮缩放 | 拖拽平移 | 拖拽节点调整位置 | 双击节点下钻
            </div>
          </>
        )}
      </div>

      {/* 图例 */}
      {!loading && !error && graphData.nodes.length > 0 && renderLegend()}
    </div>
  );
};

export default KBGraph;
