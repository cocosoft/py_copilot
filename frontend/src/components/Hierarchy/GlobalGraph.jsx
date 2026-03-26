import React, { useState, useEffect, useRef } from 'react';
import useKnowledgeStore from '../../stores/knowledgeStore';
import './GlobalGraph.css';

/**
 * 全局级图谱组件
 * 用于展示跨知识库的实体关系图谱
 */
const GlobalGraph = () => {
  const { setHierarchyLevel, setCurrentEntity, setCurrentKnowledgeBase } = useKnowledgeStore();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    nodeSize: 10,
    linkWidth: 1,
    showLabels: true,
    colorScheme: 'category10',
    showKnowledgeBaseColors: true
  });
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState('all');
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
            { id: '1', label: '人工智能', type: '领域', group: 1, knowledgeBaseId: 'kb1', knowledgeBaseName: '技术知识库' },
            { id: '2', label: '机器学习', type: '技术', group: 2, knowledgeBaseId: 'kb1', knowledgeBaseName: '技术知识库' },
            { id: '3', label: '深度学习', type: '技术', group: 2, knowledgeBaseId: 'kb1', knowledgeBaseName: '技术知识库' },
            { id: '4', label: '大数据', type: '领域', group: 3, knowledgeBaseId: 'kb2', knowledgeBaseName: '数据知识库' },
            { id: '5', label: '数据挖掘', type: '技术', group: 4, knowledgeBaseId: 'kb2', knowledgeBaseName: '数据知识库' },
            { id: '6', label: '云计算', type: '技术', group: 5, knowledgeBaseId: 'kb3', knowledgeBaseName: '云服务知识库' },
            { id: '7', label: '容器', type: '技术', group: 5, knowledgeBaseId: 'kb3', knowledgeBaseName: '云服务知识库' },
            { id: '8', label: '微服务', type: '架构', group: 6, knowledgeBaseId: 'kb3', knowledgeBaseName: '云服务知识库' }
          ],
          links: [
            { source: '1', target: '2', label: '包含' },
            { source: '2', target: '3', label: '包含' },
            { source: '2', target: '4', label: '相关' },
            { source: '4', target: '5', label: '包含' },
            { source: '3', target: '6', label: '应用于' },
            { source: '6', target: '7', label: '使用' },
            { source: '7', target: '8', label: '支持' }
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

    loadGraphData();
  }, []);

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
      a.download = 'global-graph.svg';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  /**
   * 过滤节点和连线
   */
  const getFilteredData = () => {
    if (selectedKnowledgeBase === 'all') {
      return graphData;
    }

    const filteredNodes = graphData.nodes.filter(node => node.knowledgeBaseId === selectedKnowledgeBase);
    const filteredNodeIds = new Set(filteredNodes.map(node => node.id));
    const filteredLinks = graphData.links.filter(link => 
      filteredNodeIds.has(link.source) && filteredNodeIds.has(link.target)
    );

    return { nodes: filteredNodes, links: filteredLinks };
  };

  /**
   * 获取知识库列表
   */
  const getKnowledgeBases = () => {
    const kbs = new Set(graphData.nodes.map(node => node.knowledgeBaseName));
    return Array.from(kbs);
  };

  /**
   * 处理节点双击事件，实现下钻功能
   */
  const handleNodeDoubleClick = (node) => {
    // 设置当前实体
    setCurrentEntity(node);
    // 模拟设置当前知识库（实际应根据节点数据确定）
    setCurrentKnowledgeBase({ id: node.knowledgeBaseId, name: node.knowledgeBaseName });
    // 切换到知识库级视图
    setHierarchyLevel('knowledge_base');
  };

  if (loading) {
    return (
      <div className="global-graph">
        <div className="gg-loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="global-graph">
        <div className="gg-error">{error}</div>
      </div>
    );
  }

  const filteredData = getFilteredData();
  const knowledgeBases = getKnowledgeBases();

  return (
    <div className="global-graph">
      <div className="gg-header">
        <h3>全局实体关系图谱</h3>
        <div className="gg-controls">
          <div className="gg-filter">
            <select 
              value={selectedKnowledgeBase} 
              onChange={(e) => setSelectedKnowledgeBase(e.target.value)}
            >
              <option value="all">所有知识库</option>
              {knowledgeBases.map((kb, index) => (
                <option key={`gg-kb-${index}`} value={`kb${index + 1}`}>{kb}</option>
              ))}
            </select>
          </div>
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
        <div className="gg-settings">
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
            <label>
              <input
                type="checkbox"
                name="showKnowledgeBaseColors"
                checked={settings.showKnowledgeBaseColors}
                onChange={(e) => setSettings(prev => ({ ...prev, showKnowledgeBaseColors: e.target.checked }))}
              />
              按知识库着色
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

      <div className="gg-container">
        <svg 
          ref={svgRef}
          className="gg-svg"
          style={{ transform: `scale(${zoomLevel})` }}
          width="100%"
          height="100%"
        >
          {/* 绘制连线 */}
          {filteredData.links.map((link, index) => (
            <g key={`gg-link-${index}`}>
              <line
                x1={100 + parseInt(link.source) * 150}
                y1={100 + (parseInt(link.source) % 2) * 150}
                x2={100 + parseInt(link.target) * 150}
                y2={100 + (parseInt(link.target) % 2) * 150}
                stroke="#999"
                strokeWidth={settings.linkWidth}
              />
              <text
                x={100 + (parseInt(link.source) + parseInt(link.target)) * 75}
                y={100 + ((parseInt(link.source) % 2) + (parseInt(link.target) % 2)) * 75 - 5}
                textAnchor="middle"
                fontSize="12"
                fill="#666"
              >
                {link.label}
              </text>
            </g>
          ))}

          {/* 绘制节点 */}
          {filteredData.nodes.map((node, index) => {
            const knowledgeBaseColors = {
              'kb1': '#3498db',  // 技术知识库
              'kb2': '#2ecc71',  // 数据知识库
              'kb3': '#f39c12',  // 云服务知识库
              'kb4': '#9b59b6',  // 其他知识库1
              'kb5': '#e74c3c'   // 其他知识库2
            };

            const typeColors = {
              '领域': '#3498db',
              '技术': '#2ecc71',
              '架构': '#f39c12',
              '设备': '#9b59b6',
              '组织': '#e74c3c',
              '人物': '#1abc9c',
              '地点': '#34495e'
            };
            
            const color = settings.showKnowledgeBaseColors 
              ? knowledgeBaseColors[node.knowledgeBaseId] || '#999'
              : typeColors[node.type] || '#999';
            
            return (
              <g
                key={`gg-node-${node.id}-${index}`}
                className="node-group"
                onDoubleClick={() => handleNodeDoubleClick(node)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  cx={100 + (index + 1) * 120}
                  cy={150 + (index % 2) * 200}
                  r={settings.nodeSize}
                  fill={color}
                  stroke="white"
                  strokeWidth="2"
                />
                {settings.showLabels && (
                  <text
                    x={100 + (index + 1) * 120}
                    y={150 + (index % 2) * 200 + settings.nodeSize + 15}
                    textAnchor="middle"
                    fontSize="12"
                    fill="#333"
                  >
                    {node.label}
                  </text>
                )}
                {settings.showLabels && (
                  <text
                    x={100 + (index + 1) * 120}
                    y={150 + (index % 2) * 200 - settings.nodeSize - 10}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#666"
                  >
                    {node.knowledgeBaseName}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="gg-legend">
        <h4>图例</h4>
        <div className="legend-items">
          <div className="legend-section">
            <h5>知识库</h5>
            <div className="legend-subitems">
              <div className="legend-item">
                <div className="legend-color" style={{ backgroundColor: '#3498db' }}></div>
                <span>技术知识库</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{ backgroundColor: '#2ecc71' }}></div>
                <span>数据知识库</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{ backgroundColor: '#f39c12' }}></div>
                <span>云服务知识库</span>
              </div>
            </div>
          </div>
          <div className="legend-section">
            <h5>实体类型</h5>
            <div className="legend-subitems">
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
                <span>架构</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlobalGraph;