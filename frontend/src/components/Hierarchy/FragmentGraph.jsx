import React, { useState, useEffect, useRef } from 'react';
import './FragmentGraph.css';

/**
 * 片段级图谱组件
 * 用于展示片段中的实体关系图谱
 */
const FragmentGraph = ({ fragmentId }) => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
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

  /**
   * 加载图谱数据
   */
  useEffect(() => {
    const loadGraphData = async () => {
      try {
        setLoading(true);
        setError(null);
        // 模拟API调用
        // 实际项目中应该调用真实的API
        const mockGraphData = {
          nodes: [
            { id: '1', label: '人工智能', type: '领域', group: 1 },
            { id: '2', label: '机器学习', type: '技术', group: 2 },
            { id: '3', label: '深度学习', type: '技术', group: 2 },
            { id: '4', label: '多层神经网络', type: '技术', group: 2 },
            { id: '5', label: '计算机', type: '设备', group: 3 }
          ],
          links: [
            { source: '1', target: '2', label: '包含' },
            { source: '2', target: '3', label: '包含' },
            { source: '3', target: '4', label: '使用' },
            { source: '2', target: '5', label: '运行于' }
          ]
        };

        // 模拟网络延迟
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setGraphData(mockGraphData);
      } catch (err) {
        setError('加载图谱数据失败');
        console.error('加载图谱数据失败:', err);
      } finally {
        setLoading(false);
      }
    };

    if (fragmentId) {
      loadGraphData();
    }
  }, [fragmentId]);

  /**
   * 处理设置变更
   * @param {Event} e - 输入事件
   */
  const handleSettingChange = (e) => {
    const { name, value } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: name === 'nodeSize' || name === 'linkWidth' ? parseFloat(value) : value
    }));
  };

  /**
   * 处理缩放
   * @param {number} factor - 缩放因子
   */
  const handleZoom = (factor) => {
    setZoomLevel(prev => Math.max(0.1, Math.min(3, prev * factor)));
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
    if (svgRef.current) {
      const svg = svgRef.current;
      const serializer = new XMLSerializer();
      const svgString = serializer.serializeToString(svg);
      const blob = new Blob([svgString], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fragment-graph-${fragmentId}.svg`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  if (loading) {
    return (
      <div className="fragment-graph">
        <div className="fg-loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fragment-graph">
        <div className="fg-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="fragment-graph">
      <div className="fg-header">
        <h3>片段实体关系图谱</h3>
        <div className="fg-controls">
          <button 
            className="control-button"
            onClick={() => handleZoom(0.9)}
            title="缩小"
          >
            🔍-
          </button>
          <button 
            className="control-button"
            onClick={handleReset}
            title="重置"
          >
            🔄
          </button>
          <button 
            className="control-button"
            onClick={() => handleZoom(1.1)}
            title="放大"
          >
            🔍+
          </button>
          <button 
            className="control-button"
            onClick={handleDownload}
            title="下载"
          >
            💾
          </button>
          <button 
            className="control-button"
            onClick={() => setShowSettings(!showSettings)}
            title="设置"
          >
            ⚙️
          </button>
        </div>
      </div>

      {showSettings && (
        <div className="fg-settings">
          <h4>图谱设置</h4>
          <div className="setting-item">
            <label>节点大小: {settings.nodeSize}</label>
            <input
              type="range"
              name="nodeSize"
              min="5"
              max="20"
              step="1"
              value={settings.nodeSize}
              onChange={handleSettingChange}
            />
          </div>
          <div className="setting-item">
            <label>连线宽度: {settings.linkWidth}</label>
            <input
              type="range"
              name="linkWidth"
              min="0.5"
              max="3"
              step="0.5"
              value={settings.linkWidth}
              onChange={handleSettingChange}
            />
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                name="showLabels"
                checked={settings.showLabels}
                onChange={(e) => setSettings(prev => ({ ...prev, showLabels: e.target.checked }))}
              />
              显示标签
            </label>
          </div>
          <div className="setting-item">
            <label>颜色方案:</label>
            <select
              name="colorScheme"
              value={settings.colorScheme}
              onChange={handleSettingChange}
            >
              <option value="category10">Category 10</option>
              <option value="category20">Category 20</option>
              <option value="category20b">Category 20b</option>
              <option value="category20c">Category 20c</option>
            </select>
          </div>
        </div>
      )}

      <div className="fg-container">
        <svg 
          ref={svgRef}
          className="fg-svg"
          style={{ transform: `scale(${zoomLevel})` }}
          width="100%"
          height="100%"
        >
          {/* 绘制连线 */}
          {graphData.links.map((link, index) => (
            <g key={`fg-link-${index}`}>
              <line
                x1={100 + parseInt(link.source) * 150}
                y1={100 + (parseInt(link.source) % 2) * 100}
                x2={100 + parseInt(link.target) * 150}
                y2={100 + (parseInt(link.target) % 2) * 100}
                stroke="#999"
                strokeWidth={settings.linkWidth}
              />
              <text
                x={100 + (parseInt(link.source) + parseInt(link.target)) * 75}
                y={100 + ((parseInt(link.source) % 2) + (parseInt(link.target) % 2)) * 50 - 5}
                textAnchor="middle"
                fontSize="12"
                fill="#666"
              >
                {link.label}
              </text>
            </g>
          ))}

          {/* 绘制节点 */}
          {graphData.nodes.map((node, index) => {
            const colors = {
              '领域': '#3498db',
              '技术': '#2ecc71',
              '设备': '#f39c12',
              '组织': '#9b59b6',
              '人物': '#e74c3c',
              '地点': '#1abc9c'
            };

            const color = colors[node.type] || '#999';

            return (
              <g key={`fg-node-${node.id}-${index}`} className="node-group">
                <circle
                  cx={100 + parseInt(node.id) * 150}
                  cy={100 + (parseInt(node.id) % 2) * 100}
                  r={settings.nodeSize}
                  fill={color}
                  stroke="white"
                  strokeWidth="2"
                />
                {settings.showLabels && (
                  <text
                    x={100 + parseInt(node.id) * 150}
                    y={100 + (parseInt(node.id) % 2) * 100 + settings.nodeSize + 15}
                    textAnchor="middle"
                    fontSize="12"
                    fill="#333"
                  >
                    {node.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="fg-legend">
        <h4>图例</h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#3498db' }}></div>
            <span>领域</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#2ecc71' }}></div>
            <span>技术</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#f39c12' }}></div>
            <span>设备</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#9b59b6' }}></div>
            <span>组织</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#e74c3c' }}></div>
            <span>人物</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#1abc9c' }}></div>
            <span>地点</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FragmentGraph;