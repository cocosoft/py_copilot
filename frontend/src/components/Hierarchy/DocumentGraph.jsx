/**
 * 文档图谱组件
 *
 * 用于可视化文档级别的实体关系图谱
 */

import React, { useState, useEffect, useRef } from 'react';
import { FiZoomIn, FiZoomOut, FiRotateCcw, FiDownload, FiSettings } from 'react-icons/fi';
import { getDocumentGraph } from '../../utils/api/hierarchyApi';
import './DocumentGraph.css';

const DocumentGraph = ({ knowledgeBaseId, documentId }) => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    nodeSize: 10,
    linkWidth: 1,
    showLabels: true,
    colorScheme: 'category10'
  });
  const svgRef = useRef(null);

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
      // 确保 documentId 是字符串或数字
      const docId = typeof documentId === 'object' ? documentId.id || documentId.document_id : documentId;
      console.log('[DocumentGraph] 加载图谱数据:', { knowledgeBaseId, documentId: docId });
      const response = await getDocumentGraph(knowledgeBaseId, docId);
      setGraphData({
        nodes: response.nodes || [],
        links: response.links || []
      });
    } catch (err) {
      console.error('加载文档图谱失败:', err);
      setError('加载图谱失败，请稍后重试');
      // 使用模拟数据
      setGraphData({
        nodes: [
          { id: 1, name: '张三', type: 'PERSON', group: 1 },
          { id: 2, name: '科技公司', type: 'ORGANIZATION', group: 2 },
          { id: 3, name: '北京', type: 'LOCATION', group: 3 },
          { id: 4, name: '2026年', type: 'DATE', group: 4 },
          { id: 5, name: '人工智能', type: 'CONCEPT', group: 5 },
          { id: 6, name: '李四', type: 'PERSON', group: 1 },
          { id: 7, name: '上海', type: 'LOCATION', group: 3 },
          { id: 8, name: '机器学习', type: 'CONCEPT', group: 5 },
          { id: 9, name: '2025年', type: 'DATE', group: 4 },
          { id: 10, name: '互联网公司', type: 'ORGANIZATION', group: 2 },
        ],
        links: [
          { source: 1, target: 2, type: 'WORKS_AT', value: 1 },
          { source: 1, target: 3, type: 'LOCATED_IN', value: 1 },
          { source: 1, target: 5, type: 'INTERESTED_IN', value: 1 },
          { source: 2, target: 5, type: 'DEVELOPS', value: 1 },
          { source: 2, target: 8, type: 'USES', value: 1 },
          { source: 6, target: 10, type: 'WORKS_AT', value: 1 },
          { source: 6, target: 7, type: 'LOCATED_IN', value: 1 },
          { source: 10, target: 5, type: 'RESEARCHES', value: 1 },
          { source: 1, target: 9, type: 'EVENT_DATE', value: 1 },
          { source: 6, target: 4, type: 'EVENT_DATE', value: 1 },
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理缩放
   */
  const handleZoom = (direction) => {
    if (direction === 'in' && zoomLevel < 2) {
      setZoomLevel(zoomLevel + 0.1);
    } else if (direction === 'out' && zoomLevel > 0.5) {
      setZoomLevel(zoomLevel - 0.1);
    }
  };

  /**
   * 重置视图
   */
  const handleReset = () => {
    setZoomLevel(1);
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
   * 渲染图谱
   */
  const renderGraph = () => {
    if (!graphData.nodes.length) return null;

    // 简化的图谱渲染，实际项目中可以使用D3.js
    return (
      <div className="graph-container" style={{ transform: `scale(${zoomLevel})` }}>
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox="0 0 800 600"
          className="graph-svg"
        >
          {/* 绘制连接线 */}
          {graphData.links.map((link, index) => (
            <line
              key={`dg-link-${index}`}
              x1={Math.random() * 700 + 50}
              y1={Math.random() * 500 + 50}
              x2={Math.random() * 700 + 50}
              y2={Math.random() * 500 + 50}
              stroke="#999"
              strokeWidth={settings.linkWidth}
              strokeOpacity="0.6"
            />
          ))}

          {/* 绘制节点 */}
          {graphData.nodes.map((node, index) => (
            <g key={`dg-node-${node.id}-${index}`}>
              <circle
                cx={Math.random() * 700 + 50}
                cy={Math.random() * 500 + 50}
                r={settings.nodeSize}
                fill={`hsl(${node.group * 36}, 70%, 60%)`}
                stroke="#fff"
                strokeWidth="1.5"
              />
              {settings.showLabels && (
                <text
                  x={Math.random() * 700 + 50}
                  y={Math.random() * 500 + 50 + settings.nodeSize + 10}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#333"
                >
                  {node.name}
                </text>
              )}
            </g>
          ))}
        </svg>
      </div>
    );
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
              min="5"
              max="20"
              value={settings.nodeSize}
              onChange={(e) => handleSettingChange('nodeSize', parseInt(e.target.value))}
            />
            <span>{settings.nodeSize}</span>
          </div>
          <div className="setting-item">
            <label>连接线宽度:</label>
            <input
              type="range"
              min="0.5"
              max="3"
              step="0.5"
              value={settings.linkWidth}
              onChange={(e) => handleSettingChange('linkWidth', parseFloat(e.target.value))}
            />
            <span>{settings.linkWidth}</span>
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
      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : graphData.nodes.length === 0 ? (
        <div className="empty">暂无图谱数据</div>
      ) : (
        <div className="dg-content">
          {renderGraph()}
          <div className="graph-info">
            节点: {graphData.nodes.length} | 连接: {graphData.links.length}
          </div>
        </div>
      )}

      {/* 图例 */}
      {graphData.nodes.length > 0 && (
        <div className="graph-legend">
          <h4>图例</h4>
          <div className="legend-items">
            {[...new Set(graphData.nodes.map(node => node.type))].map((type, index) => (
              <div key={`dg-legend-${type}-${index}`} className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: `hsl(${(index + 1) * 36}, 70%, 60%)` }}
                ></div>
                <span>{type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentGraph;