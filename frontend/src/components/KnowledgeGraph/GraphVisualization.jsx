/**
 * 图谱可视化组件
 *
 * 提供知识图谱的可视化展示功能，包含社区发现、中心性分析等分析工具
 */

import React, { useState, useEffect } from 'react';
import KnowledgeGraph from '../KnowledgeGraph';
import {
  analyzeCommunities,
  analyzeCentrality,
  findPath
} from '../../utils/api/knowledgeGraphApi';
import './GraphVisualization.css';

/**
 * 图谱可视化组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @returns {JSX.Element} 图谱可视化界面
 */
const GraphVisualization = ({ knowledgeBaseId }) => {
  // 图谱数据
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 视图模式
  const [viewMode, setViewMode] = useState('force'); // force, hierarchical
  // 筛选条件
  const [filters, setFilters] = useState({
    entityTypes: [],
    relationTypes: [],
    minConfidence: 0.5
  });
  // 当前激活的分析工具
  const [activeTool, setActiveTool] = useState(null); // null, 'community', 'centrality', 'path'
  // 分析结果
  const [analysisResult, setAnalysisResult] = useState(null);
  // 路径分析的起点和终点
  const [pathStart, setPathStart] = useState('');
  const [pathEnd, setPathEnd] = useState('');
  // 选中的节点
  const [selectedNode, setSelectedNode] = useState(null);

  // 加载图谱数据
  useEffect(() => {
    if (!knowledgeBaseId) return;

    loadGraphData();
  }, [knowledgeBaseId]);

  const loadGraphData = async () => {
    setLoading(true);
    // TODO: 调用API获取图谱数据
    // Mock数据
    setTimeout(() => {
      const mockData = {
        nodes: [
          { id: 1, name: '张三', type: 'PERSON', confidence: 0.95 },
          { id: 2, name: 'ABC公司', type: 'ORG', confidence: 0.92 },
          { id: 3, name: '北京', type: 'LOCATION', confidence: 0.98 },
          { id: 4, name: '李四', type: 'PERSON', confidence: 0.91 },
          { id: 5, name: 'XYZ科技', type: 'ORG', confidence: 0.89 },
          { id: 6, name: '王五', type: 'PERSON', confidence: 0.87 },
          { id: 7, name: '上海', type: 'LOCATION', confidence: 0.96 },
          { id: 8, name: 'DEF集团', type: 'ORG', confidence: 0.90 }
        ],
        edges: [
          { source: 1, target: 2, type: '就职于', confidence: 0.88 },
          { source: 2, target: 3, type: '位于', confidence: 0.95 },
          { source: 4, target: 2, type: '就职于', confidence: 0.85 },
          { source: 1, target: 4, type: '同事', confidence: 0.78 },
          { source: 5, target: 7, type: '位于', confidence: 0.92 },
          { source: 6, target: 5, type: '就职于', confidence: 0.86 },
          { source: 2, target: 8, type: '合作', confidence: 0.75 },
          { source: 8, target: 7, type: '位于', confidence: 0.94 }
        ]
      };
      setGraphData(mockData);
      setLoading(false);
    }, 1000);
  };

  // 执行社区发现分析
  const handleCommunityAnalysis = async () => {
    setActiveTool('community');
    setLoading(true);

    try {
      const result = await analyzeCommunities(knowledgeBaseId);
      setAnalysisResult({
        type: 'community',
        data: result
      });
    } catch (error) {
      console.error('社区发现分析失败:', error);
      // Mock数据
      setAnalysisResult({
        type: 'community',
        data: {
          communities: [
            {
              id: 1,
              name: '社区 1',
              nodes: ['张三', '李四', 'ABC公司', '北京'],
              size: 4,
              density: 0.75
            },
            {
              id: 2,
              name: '社区 2',
              nodes: ['王五', 'XYZ科技', '上海'],
              size: 3,
              density: 0.67
            },
            {
              id: 3,
              name: '社区 3',
              nodes: ['DEF集团', '上海'],
              size: 2,
              density: 1.0
            }
          ],
          modularity: 0.45
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // 执行中心性分析
  const handleCentralityAnalysis = async () => {
    setActiveTool('centrality');
    setLoading(true);

    try {
      const result = await analyzeCentrality(knowledgeBaseId);
      setAnalysisResult({
        type: 'centrality',
        data: result
      });
    } catch (error) {
      console.error('中心性分析失败:', error);
      // Mock数据
      setAnalysisResult({
        type: 'centrality',
        data: {
          degree: [
            { node: 'ABC公司', value: 0.85 },
            { node: '北京', value: 0.65 },
            { node: '张三', value: 0.55 },
            { node: '李四', value: 0.45 },
            { node: '上海', value: 0.40 }
          ],
          betweenness: [
            { node: 'ABC公司', value: 0.72 },
            { node: '张三', value: 0.48 },
            { node: '北京', value: 0.35 },
            { node: '李四', value: 0.28 },
            { node: 'DEF集团', value: 0.20 }
          ],
          closeness: [
            { node: 'ABC公司', value: 0.78 },
            { node: '张三', value: 0.71 },
            { node: '李四', value: 0.68 },
            { node: '北京', value: 0.65 },
            { node: '上海', value: 0.58 }
          ]
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // 执行路径发现
  const handlePathFind = async () => {
    if (!pathStart || !pathEnd) return;

    setActiveTool('path');
    setLoading(true);

    try {
      const result = await findPath(knowledgeBaseId, pathStart, pathEnd);
      setAnalysisResult({
        type: 'path',
        data: result
      });
    } catch (error) {
      console.error('路径发现失败:', error);
      // Mock数据
      setAnalysisResult({
        type: 'path',
        data: {
          paths: [
            {
              nodes: ['张三', 'ABC公司', 'DEF集团', '上海'],
              edges: ['就职于', '合作', '位于'],
              length: 3
            },
            {
              nodes: ['张三', '李四', 'ABC公司', 'DEF集团', '上海'],
              edges: ['同事', '就职于', '合作', '位于'],
              length: 4
            }
          ],
          shortestPathLength: 3
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // 获取实体类型颜色
  const getEntityTypeColor = (type) => {
    const colorMap = {
      'PERSON': '#3b82f6',
      'ORG': '#10b981',
      'LOCATION': '#f59e0b',
      'TIME': '#8b5cf6',
      'EVENT': '#ef4444',
      'CONCEPT': '#6b7280',
      'PRODUCT': '#ec4899'
    };
    return colorMap[type] || '#6b7280';
  };

  // 获取实体类型标签
  const getEntityTypeLabel = (type) => {
    const typeMap = {
      'PERSON': '人物',
      'ORG': '组织',
      'LOCATION': '地点',
      'TIME': '时间',
      'EVENT': '事件',
      'CONCEPT': '概念',
      'PRODUCT': '产品'
    };
    return typeMap[type] || type;
  };

  // 渲染分析结果
  const renderAnalysisResult = () => {
    if (!analysisResult) return null;

    switch (analysisResult.type) {
      case 'community':
        return (
          <div className="analysis-result community-result">
            <h4>社区发现结果</h4>
            <div className="modularity-score">
              模块度: {analysisResult.data.modularity?.toFixed(3) || 'N/A'}
            </div>
            <div className="communities-list">
              {analysisResult.data.communities?.map(community => (
                <div key={community.id} className="community-card">
                  <div className="community-header">
                    <span className="community-name">{community.name}</span>
                    <span className="community-size">{community.size} 节点</span>
                  </div>
                  <div className="community-density">
                    密度: {(community.density * 100).toFixed(1)}%
                  </div>
                  <div className="community-nodes">
                    {community.nodes.map((node, index) => (
                      <span key={index} className="community-node-tag">{node}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'centrality':
        return (
          <div className="analysis-result centrality-result">
            <h4>中心性分析结果</h4>
            <div className="centrality-tabs">
              <div className="centrality-section">
                <h5>度中心性 (Top 5)</h5>
                <div className="centrality-list">
                  {analysisResult.data.degree?.map((item, index) => (
                    <div key={index} className="centrality-item">
                      <span className="rank">#{index + 1}</span>
                      <span className="node-name">{item.node}</span>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${item.value * 100}%` }}></div>
                      </div>
                      <span className="score-value">{item.value.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="centrality-section">
                <h5>介数中心性 (Top 5)</h5>
                <div className="centrality-list">
                  {analysisResult.data.betweenness?.map((item, index) => (
                    <div key={index} className="centrality-item">
                      <span className="rank">#{index + 1}</span>
                      <span className="node-name">{item.node}</span>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${item.value * 100}%` }}></div>
                      </div>
                      <span className="score-value">{item.value.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="centrality-section">
                <h5>接近中心性 (Top 5)</h5>
                <div className="centrality-list">
                  {analysisResult.data.closeness?.map((item, index) => (
                    <div key={index} className="centrality-item">
                      <span className="rank">#{index + 1}</span>
                      <span className="node-name">{item.node}</span>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${item.value * 100}%` }}></div>
                      </div>
                      <span className="score-value">{item.value.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'path':
        return (
          <div className="analysis-result path-result">
            <h4>路径发现结果</h4>
            <div className="path-info">
              从 <strong>{pathStart}</strong> 到 <strong>{pathEnd}</strong>
            </div>
            <div className="paths-list">
              {analysisResult.data.paths?.map((path, index) => (
                <div key={index} className="path-card">
                  <div className="path-header">
                    <span className="path-label">路径 {index + 1}</span>
                    <span className="path-length">长度: {path.length}</span>
                  </div>
                  <div className="path-nodes">
                    {path.nodes.map((node, nodeIndex) => (
                      <React.Fragment key={nodeIndex}>
                        <span className="path-node">{node}</span>
                        {nodeIndex < path.nodes.length - 1 && (
                          <span className="path-edge">
                            → {path.edges[nodeIndex]} →
                          </span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (loading && !graphData.nodes.length) {
    return (
      <div className="graph-visualization-loading">
        <div className="spinner"></div>
        <p>加载图谱数据...</p>
      </div>
    );
  }

  return (
    <div className="graph-visualization">
      {/* 工具栏 */}
      <div className="visualization-toolbar">
        <div className="toolbar-section">
          <span className="toolbar-label">视图模式:</span>
          <div className="view-modes">
            <button
              className={`mode-btn ${viewMode === 'force' ? 'active' : ''}`}
              onClick={() => setViewMode('force')}
            >
              力导向图
            </button>
            <button
              className={`mode-btn ${viewMode === 'hierarchical' ? 'active' : ''}`}
              onClick={() => setViewMode('hierarchical')}
            >
              层次图
            </button>
          </div>
        </div>

        <div className="toolbar-section">
          <span className="toolbar-label">分析工具:</span>
          <div className="analysis-tools">
            <button
              className={`tool-btn ${activeTool === 'community' ? 'active' : ''}`}
              onClick={handleCommunityAnalysis}
            >
              🏘️ 社区发现
            </button>
            <button
              className={`tool-btn ${activeTool === 'centrality' ? 'active' : ''}`}
              onClick={handleCentralityAnalysis}
            >
              📊 中心性分析
            </button>
            <button
              className={`tool-btn ${activeTool === 'path' ? 'active' : ''}`}
              onClick={() => setActiveTool(activeTool === 'path' ? null : 'path')}
            >
              🛤️ 路径发现
            </button>
          </div>
        </div>

        <div className="graph-actions">
          <button className="action-btn" title="放大">➕</button>
          <button className="action-btn" title="缩小">➖</button>
          <button className="action-btn" title="重置">⟲</button>
        </div>
      </div>

      {/* 路径发现输入 */}
      {activeTool === 'path' && (
        <div className="path-input-panel">
          <div className="path-inputs">
            <div className="input-group">
              <label>起点:</label>
              <select
                value={pathStart}
                onChange={(e) => setPathStart(e.target.value)}
              >
                <option value="">选择起点</option>
                {graphData.nodes.map(node => (
                  <option key={node.id} value={node.name}>{node.name}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label>终点:</label>
              <select
                value={pathEnd}
                onChange={(e) => setPathEnd(e.target.value)}
              >
                <option value="">选择终点</option>
                {graphData.nodes.map(node => (
                  <option key={node.id} value={node.name}>{node.name}</option>
                ))}
              </select>
            </div>
            <button
              className="find-path-btn"
              onClick={handlePathFind}
              disabled={!pathStart || !pathEnd}
            >
              查找路径
            </button>
          </div>
        </div>
      )}

      {/* 主内容区域 */}
      <div className="visualization-content">
        {/* 左侧：图谱可视化 */}
        <div className={`graph-panel ${analysisResult ? 'with-analysis' : ''}`}>
          {/* 筛选面板 */}
          <div className="filter-panel">
            <h4>筛选条件</h4>
            <div className="filter-group">
              <label>最小置信度: {(filters.minConfidence * 100).toFixed(0)}%</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={filters.minConfidence}
                onChange={(e) => setFilters({ ...filters, minConfidence: parseFloat(e.target.value) })}
              />
            </div>

            <div className="filter-group">
              <label>实体类型:</label>
              <div className="entity-type-filters">
                {['PERSON', 'ORG', 'LOCATION', 'TIME', 'EVENT', 'CONCEPT'].map(type => (
                  <label key={type} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={filters.entityTypes.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFilters({ ...filters, entityTypes: [...filters.entityTypes, type] });
                        } else {
                          setFilters({ ...filters, entityTypes: filters.entityTypes.filter(t => t !== type) });
                        }
                      }}
                    />
                    <span
                      className="type-color"
                      style={{ backgroundColor: getEntityTypeColor(type) }}
                    ></span>
                    {getEntityTypeLabel(type)}
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* 图谱展示区域 */}
          <div className="graph-display">
            {graphData.nodes.length > 0 ? (
              <KnowledgeGraph
                data={graphData}
                viewMode={viewMode}
                filters={filters}
                onNodeClick={setSelectedNode}
              />
            ) : (
              <div className="empty-graph">
                <span className="empty-icon">🕸️</span>
                <p>暂无图谱数据</p>
              </div>
            )}
          </div>

          {/* 节点详情 */}
          {selectedNode && (
            <div className="node-detail-panel">
              <div className="node-detail-header">
                <h4>节点详情</h4>
                <button className="close-btn" onClick={() => setSelectedNode(null)}>×</button>
              </div>
              <div className="node-detail-content">
                <div className="node-name">{selectedNode.name}</div>
                <div className="node-type">
                  <span
                    className="type-badge"
                    style={{ backgroundColor: getEntityTypeColor(selectedNode.type) }}
                  >
                    {getEntityTypeLabel(selectedNode.type)}
                  </span>
                </div>
                <div className="node-confidence">
                  置信度: {(selectedNode.confidence * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 右侧：分析结果面板 */}
        {analysisResult && (
          <div className="analysis-panel">
            <div className="analysis-panel-header">
              <h4>分析结果</h4>
              <button className="close-btn" onClick={() => setAnalysisResult(null)}>×</button>
            </div>
            <div className="analysis-panel-content">
              {renderAnalysisResult()}
            </div>
          </div>
        )}
      </div>

      {/* 图例 */}
      <div className="graph-legend">
        <h4>图例</h4>
        <div className="legend-items">
          {['PERSON', 'ORG', 'LOCATION', 'TIME', 'EVENT', 'CONCEPT'].map(type => (
            <div key={type} className="legend-item">
              <span
                className="legend-color"
                style={{ backgroundColor: getEntityTypeColor(type) }}
              ></span>
              <span className="legend-label">{getEntityTypeLabel(type)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default GraphVisualization;
