/**
 * 知识库知识图谱组件
 *
 * 用于可视化知识库级别的实体关系图谱
 */

import React, { useState, useEffect, useRef } from 'react';
import { FiZoomIn, FiZoomOut, FiRotateCcw, FiDownload, FiSettings, FiX } from 'react-icons/fi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import './KBGraph.css';

const KBGraph = ({ knowledgeBaseId }) => {
  const { setHierarchyLevel, setCurrentEntity } = useKnowledgeStore();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    nodeSize: 10,
    linkWidth: 1,
    showLabels: true,
    colorScheme: 'category10',
    layout: 'force',
    showLegend: true
  });
  const svgRef = useRef(null);

  useEffect(() => {
    if (knowledgeBaseId) {
      loadGraphData();
    }
  }, [knowledgeBaseId]);

  /**
   * 加载知识库图谱数据
   */
  const loadGraphData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 这里应该调用API获取图谱数据
      // 暂时使用模拟数据
      setGraphData({
        nodes: [
          { id: 1, name: '人工智能', type: 'CONCEPT', count: 20 },
          { id: 2, name: '机器学习', type: 'CONCEPT', count: 18 },
          { id: 3, name: '深度学习', type: 'CONCEPT', count: 15 },
          { id: 4, name: '神经网络', type: 'CONCEPT', count: 12 },
          { id: 5, name: '计算机视觉', type: 'CONCEPT', count: 10 },
          { id: 6, name: '自然语言处理', type: 'CONCEPT', count: 9 },
          { id: 7, name: '张三', type: 'PERSON', count: 5 },
          { id: 8, name: '科技公司', type: 'ORGANIZATION', count: 4 },
          { id: 9, name: '北京', type: 'LOCATION', count: 3 },
          { id: 10, name: '2026年', type: 'DATE', count: 2 }
        ],
        links: [
          { source: 1, target: 2, value: 5, label: '包含' },
          { source: 2, target: 3, value: 4, label: '包含' },
          { source: 3, target: 4, value: 3, label: '包含' },
          { source: 1, target: 5, value: 3, label: '包含' },
          { source: 1, target: 6, value: 3, label: '包含' },
          { source: 7, target: 1, value: 2, label: '研究' },
          { source: 8, target: 1, value: 2, label: '开发' },
          { source: 7, target: 8, value: 1, label: '工作' },
          { source: 8, target: 9, value: 1, label: '位于' },
          { source: 1, target: 10, value: 1, label: '预测' }
        ]
      });
    } catch (err) {
      console.error('加载知识库图谱失败:', err);
      setError('加载图谱失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理缩放
   */
  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev * 1.2, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev / 1.2, 0.5));
  };

  const handleResetZoom = () => {
    setZoomLevel(1);
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
  const handleSettingsChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  /**
   * 处理节点双击事件，实现下钻功能
   */
  const handleNodeDoubleClick = (node) => {
    // 设置当前实体
    setCurrentEntity(node);
    // 切换到文档级视图
    setHierarchyLevel('document');
  };

  /**
   * 获取节点颜色
   */
  const getNodeColor = (type) => {
    const colorMap = {
      CONCEPT: '#1890ff',
      PERSON: '#ff6b6b',
      ORGANIZATION: '#4ecdc4',
      LOCATION: '#45b7d1',
      DATE: '#96ceb4',
      MONEY: '#feca57',
      TECH: '#a29bfe',
      PRODUCT: '#fd79a8',
      EVENT: '#fdcb6e'
    };
    return colorMap[type] || '#666666';
  };

  /**
   * 生成图谱SVG
   */
  const renderGraph = () => {
    if (!graphData.nodes || graphData.nodes.length === 0) {
      return <div className="no-data">暂无数据</div>;
    }

    // 简单的力导向布局模拟
    const width = 800;
    const height = 600;
    const centerX = width / 2;
    const centerY = height / 2;

    // 计算节点位置（简单圆形布局）
    const nodePositions = {};
    const radius = Math.min(width, height) * 0.4;
    graphData.nodes.forEach((node, index) => {
      const angle = (index / graphData.nodes.length) * Math.PI * 2;
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    return (
      <svg 
        ref={svgRef}
        width={width} 
        height={height} 
        className="graph-svg"
        style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
      >
        {/* 绘制连线 */}
        {graphData.links.map((link, index) => {
          const sourcePos = nodePositions[link.source];
          const targetPos = nodePositions[link.target];
          if (!sourcePos || !targetPos) return null;

          return (
            <g key={`kbg-link-${index}`}>
              <line
                x1={sourcePos.x}
                y1={sourcePos.y}
                x2={targetPos.x}
                y2={targetPos.y}
                stroke="#999999"
                strokeWidth={settings.linkWidth}
                strokeOpacity={0.6}
              />
              {settings.showLabels && link.label && (
                <text
                  x={(sourcePos.x + targetPos.x) / 2}
                  y={(sourcePos.y + targetPos.y) / 2 - 5}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#666666"
                >
                  {link.label}
                </text>
              )}
            </g>
          );
        })}

        {/* 绘制节点 */}
        {graphData.nodes.map((node, index) => {
          const pos = nodePositions[node.id];
          if (!pos) return null;

          return (
            <g
              key={`kbg-node-${node.id}-${index}`}
              className="graph-node"
              data-id={node.id}
              onDoubleClick={() => handleNodeDoubleClick(node)}
              style={{ cursor: 'pointer' }}
            >
              <circle
                cx={pos.x}
                cy={pos.y}
                r={Math.max(settings.nodeSize, node.count * 0.5)}
                fill={getNodeColor(node.type)}
                stroke="#ffffff"
                strokeWidth={2}
                opacity={0.8}
              />
              {settings.showLabels && (
                <text
                  x={pos.x}
                  y={pos.y + Math.max(settings.nodeSize, node.count * 0.5) + 15}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#333333"
                  fontWeight="500"
                >
                  {node.name}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    );
  };

  /**
   * 渲染图例
   */
  const renderLegend = () => {
    if (!settings.showLegend) return null;

    const entityTypes = [
      { type: 'CONCEPT', label: '概念' },
      { type: 'PERSON', label: '人物' },
      { type: 'ORGANIZATION', label: '组织' },
      { type: 'LOCATION', label: '地点' },
      { type: 'DATE', label: '日期' },
      { type: 'MONEY', label: '金额' },
      { type: 'TECH', label: '技术' },
      { type: 'PRODUCT', label: '产品' },
      { type: 'EVENT', label: '事件' }
    ];

    return (
      <div className="graph-legend">
        <h4>图例</h4>
        <div className="legend-items">
          {entityTypes.map((item, index) => (
            <div key={`kbg-legend-${item.type}-${index}`} className="legend-item">
              <div 
                className="legend-color" 
                style={{ backgroundColor: getNodeColor(item.type) }}
              ></div>
              <span className="legend-label">{item.label}</span>
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
            onClick={handleZoomIn}
            title="放大"
          >
            <FiZoomIn />
          </button>
          <button
            className="control-btn"
            onClick={handleZoomOut}
            title="缩小"
          >
            <FiZoomOut />
          </button>
          <button
            className="control-btn"
            onClick={handleResetZoom}
            title="重置缩放"
          >
            <FiRotateCcw />
          </button>
          <button
            className="control-btn"
            onClick={handleDownload}
            title="下载图谱数据"
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

      {/* 图谱设置面板 */}
      {showSettings && (
        <div className="graph-settings">
          <div className="settings-header">
            <h4>图谱设置</h4>
            <button
              className="close-btn"
              onClick={() => setShowSettings(false)}
            >
              <FiX />
            </button>
          </div>
          <div className="settings-content">
            <div className="setting-item">
              <label>节点大小:</label>
              <input
                type="range"
                min="5"
                max="20"
                value={settings.nodeSize}
                onChange={(e) => handleSettingsChange('nodeSize', parseInt(e.target.value))}
              />
              <span>{settings.nodeSize}</span>
            </div>
            <div className="setting-item">
              <label>连线宽度:</label>
              <input
                type="range"
                min="0.5"
                max="3"
                step="0.5"
                value={settings.linkWidth}
                onChange={(e) => handleSettingsChange('linkWidth', parseFloat(e.target.value))}
              />
              <span>{settings.linkWidth}</span>
            </div>
            <div className="setting-item checkbox">
              <input
                type="checkbox"
                id="show-labels"
                checked={settings.showLabels}
                onChange={(e) => handleSettingsChange('showLabels', e.target.checked)}
              />
              <label htmlFor="show-labels">显示标签</label>
            </div>
            <div className="setting-item checkbox">
              <input
                type="checkbox"
                id="show-legend"
                checked={settings.showLegend}
                onChange={(e) => handleSettingsChange('showLegend', e.target.checked)}
              />
              <label htmlFor="show-legend">显示图例</label>
            </div>
            <div className="setting-item">
              <label>布局方式:</label>
              <select
                value={settings.layout}
                onChange={(e) => handleSettingsChange('layout', e.target.value)}
              >
                <option value="force">力导向布局</option>
                <option value="circular">环形布局</option>
                <option value="hierarchical">层次布局</option>
              </select>
            </div>
            <div className="setting-item">
              <label>颜色方案:</label>
              <select
                value={settings.colorScheme}
                onChange={(e) => handleSettingsChange('colorScheme', e.target.value)}
              >
                <option value="category10">Category 10</option>
                <option value="category20">Category 20</option>
                <option value="viridis">Viridis</option>
                <option value="plasma">Plasma</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* 图谱内容 */}
      <div className="kb-graph-content">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : (
          <div className="graph-container">
            {renderGraph()}
            {renderLegend()}
          </div>
        )}
      </div>

      {/* 统计信息 */}
      <div className="kb-graph-stats">
        <span className="stat-item">
          节点: <strong>{graphData.nodes.length}</strong>
        </span>
        <span className="stat-item">
          连线: <strong>{graphData.links.length}</strong>
        </span>
      </div>
    </div>
  );
};

export default KBGraph;