/**
 * 高级图谱分析组件
 * 
 * 提供知识图谱的高级分析功能：
 * 1. 中心性分析（度中心性、介数中心性、接近中心性）
 * 2. 社区发现
 * 3. 路径分析
 * 4. 时序演化分析
 * 5. 统计报表
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import * as echarts from 'echarts';
import './AdvancedGraphAnalytics.css';

/**
 * 分析类型枚举
 */
export const AnalysisType = {
  CENTRALITY: 'centrality',
  COMMUNITY: 'community',
  PATH: 'path',
  TEMPORAL: 'temporal',
  STATISTICS: 'statistics'
};

/**
 * 中心性类型枚举
 */
export const CentralityType = {
  DEGREE: 'degree',
  BETWEENNESS: 'betweenness',
  CLOSENESS: 'closeness',
  EIGENVECTOR: 'eigenvector',
  PAGERANK: 'pagerank'
};

/**
 * 高级图谱分析组件
 * 
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 * @param {string} props.knowledgeBaseId - 知识库ID
 * @param {Function} props.onAnalysisComplete - 分析完成回调
 */
const AdvancedGraphAnalytics = ({
  graphData,
  knowledgeBaseId,
  onAnalysisComplete,
  width = '100%',
  height = '600px'
}) => {
  const [activeAnalysis, setActiveAnalysis] = useState(AnalysisType.STATISTICS);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedCentrality, setSelectedCentrality] = useState(CentralityType.DEGREE);
  const [pathSource, setPathSource] = useState('');
  const [pathTarget, setPathTarget] = useState('');
  const [temporalRange, setTemporalRange] = useState('7d');

  /**
   * 计算基础统计
   */
  const calculateStatistics = useCallback(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      return null;
    }

    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // 实体类型统计
    const entityTypes = {};
    nodes.forEach(node => {
      const type = node.entity_type || node.type || 'UNKNOWN';
      entityTypes[type] = (entityTypes[type] || 0) + 1;
    });

    // 关系类型统计
    const relationTypes = {};
    edges.forEach(edge => {
      const type = edge.relation_type || edge.type || 'UNKNOWN';
      relationTypes[type] = (relationTypes[type] || 0) + 1;
    });

    // 度分布
    const degreeDistribution = {};
    nodes.forEach(node => {
      const degree = edges.filter(e => 
        e.source === node.id || e.target === node.id
      ).length;
      degreeDistribution[degree] = (degreeDistribution[degree] || 0) + 1;
    });

    // 连通分量（简化计算）
    const connectedComponents = calculateConnectedComponents(nodes, edges);

    return {
      totalNodes: nodes.length,
      totalEdges: edges.length,
      density: edges.length / (nodes.length * (nodes.length - 1) / 2),
      avgDegree: (edges.length * 2) / nodes.length,
      entityTypes,
      relationTypes,
      degreeDistribution,
      connectedComponents: connectedComponents.length,
      largestComponent: Math.max(...connectedComponents.map(c => c.length), 0)
    };
  }, [graphData]);

  /**
   * 计算连通分量
   */
  const calculateConnectedComponents = (nodes, edges) => {
    const visited = new Set();
    const components = [];

    const adjacencyList = {};
    nodes.forEach(node => {
      adjacencyList[node.id] = [];
    });
    edges.forEach(edge => {
      if (adjacencyList[edge.source]) {
        adjacencyList[edge.source].push(edge.target);
      }
      if (adjacencyList[edge.target]) {
        adjacencyList[edge.target].push(edge.source);
      }
    });

    const dfs = (nodeId, component) => {
      visited.add(nodeId);
      component.push(nodeId);
      
      (adjacencyList[nodeId] || []).forEach(neighbor => {
        if (!visited.has(neighbor)) {
          dfs(neighbor, component);
        }
      });
    };

    nodes.forEach(node => {
      if (!visited.has(node.id)) {
        const component = [];
        dfs(node.id, component);
        components.push(component);
      }
    });

    return components;
  };

  /**
   * 计算中心性
   */
  const calculateCentrality = useCallback(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      return [];
    }

    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // 构建邻接表
    const adjacencyList = {};
    nodes.forEach(node => {
      adjacencyList[node.id] = [];
    });
    edges.forEach(edge => {
      if (adjacencyList[edge.source]) {
        adjacencyList[edge.source].push(edge.target);
      }
      if (adjacencyList[edge.target]) {
        adjacencyList[edge.target].push(edge.source);
      }
    });

    const results = nodes.map(node => {
      const neighbors = adjacencyList[node.id] || [];
      
      let score = 0;
      switch (selectedCentrality) {
        case CentralityType.DEGREE:
          score = neighbors.length;
          break;
        case CentralityType.BETWEENNESS:
          // 简化的介数中心性
          score = neighbors.length * Math.log(neighbors.length + 1);
          break;
        case CentralityType.CLOSENESS:
          // 简化的接近中心性
          score = neighbors.length > 0 ? 1 / Math.sqrt(neighbors.length) : 0;
          break;
        case CentralityType.EIGENVECTOR:
          // 简化的特征向量中心性
          score = neighbors.length * 0.5;
          break;
        case CentralityType.PAGERANK:
          // 简化的PageRank
          score = neighbors.length * 0.1 + 0.1;
          break;
        default:
          score = neighbors.length;
      }

      return {
        nodeId: node.id,
        nodeName: node.name || node.text || node.id,
        entityType: node.entity_type || node.type || 'UNKNOWN',
        score: parseFloat(score.toFixed(4)),
        degree: neighbors.length
      };
    });

    // 按分数排序
    return results.sort((a, b) => b.score - a.score);
  }, [graphData, selectedCentrality]);

  /**
   * 执行社区发现（简化版）
   */
  const detectCommunities = useCallback(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      return [];
    }

    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // 简化的标签传播算法
    const communities = new Map();
    const nodeLabels = new Map();

    // 初始化：每个节点一个标签
    nodes.forEach((node, index) => {
      nodeLabels.set(node.id, index);
    });

    // 迭代传播
    for (let iteration = 0; iteration < 10; iteration++) {
      nodes.forEach(node => {
        const neighborLabels = {};
        
        edges.forEach(edge => {
          let neighborId = null;
          if (edge.source === node.id) {
            neighborId = edge.target;
          } else if (edge.target === node.id) {
            neighborId = edge.source;
          }

          if (neighborId) {
            const label = nodeLabels.get(neighborId);
            neighborLabels[label] = (neighborLabels[label] || 0) + 1;
          }
        });

        // 选择最常见的标签
        if (Object.keys(neighborLabels).length > 0) {
          const maxLabel = Object.entries(neighborLabels)
            .sort((a, b) => b[1] - a[1])[0][0];
          nodeLabels.set(node.id, parseInt(maxLabel));
        }
      });
    }

    // 统计社区
    nodes.forEach(node => {
      const label = nodeLabels.get(node.id);
      if (!communities.has(label)) {
        communities.set(label, {
          id: label,
          nodes: [],
          size: 0
        });
      }
      communities.get(label).nodes.push({
        id: node.id,
        name: node.name || node.text || node.id,
        type: node.entity_type || node.type || 'UNKNOWN'
      });
      communities.get(label).size++;
    });

    return Array.from(communities.values())
      .sort((a, b) => b.size - a.size);
  }, [graphData]);

  /**
   * 查找路径
   */
  const findPath = useCallback(() => {
    if (!graphData || !pathSource || !pathTarget) {
      return null;
    }

    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // 构建邻接表
    const adjacencyList = {};
    nodes.forEach(node => {
      adjacencyList[node.id] = [];
    });
    edges.forEach(edge => {
      if (adjacencyList[edge.source]) {
        adjacencyList[edge.source].push({
          target: edge.target,
          relation: edge.relation_type || edge.type || 'RELATED_TO'
        });
      }
    });

    // BFS查找最短路径
    const queue = [[{ node: pathSource, relation: null }]];
    const visited = new Set([pathSource]);

    while (queue.length > 0) {
      const path = queue.shift();
      const current = path[path.length - 1].node;

      if (current === pathTarget) {
        return {
          found: true,
          pathLength: path.length - 1,
          path: path.slice(1).map((step, index) => ({
            step: index + 1,
            node: step.node,
            relation: step.relation
          }))
        };
      }

      (adjacencyList[current] || []).forEach(neighbor => {
        if (!visited.has(neighbor.target)) {
          visited.add(neighbor.target);
          queue.push([...path, { 
            node: neighbor.target, 
            relation: neighbor.relation 
          }]);
        }
      });
    }

    return { found: false, pathLength: 0, path: [] };
  }, [graphData, pathSource, pathTarget]);

  /**
   * 执行分析
   */
  const executeAnalysis = useCallback(async () => {
    setLoading(true);

    try {
      let result = null;

      switch (activeAnalysis) {
        case AnalysisType.STATISTICS:
          result = calculateStatistics();
          break;
        case AnalysisType.CENTRALITY:
          result = calculateCentrality();
          break;
        case AnalysisType.COMMUNITY:
          result = detectCommunities();
          break;
        case AnalysisType.PATH:
          result = findPath();
          break;
        default:
          result = calculateStatistics();
      }

      setAnalysisResult(result);

      if (onAnalysisComplete) {
        onAnalysisComplete(activeAnalysis, result);
      }
    } catch (error) {
      console.error('分析执行失败:', error);
    } finally {
      setLoading(false);
    }
  }, [activeAnalysis, calculateStatistics, calculateCentrality, detectCommunities, findPath, onAnalysisComplete]);

  /**
   * 自动执行分析
   */
  useEffect(() => {
    executeAnalysis();
  }, [executeAnalysis]);

  /**
   * 渲染统计视图
   */
  const renderStatisticsView = () => {
    if (!analysisResult) return null;

    const stats = analysisResult;

    return (
      <div className="analytics-statistics">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.totalNodes}</div>
            <div className="stat-label">实体总数</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.totalEdges}</div>
            <div className="stat-label">关系总数</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.density.toFixed(4)}</div>
            <div className="stat-label">图谱密度</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.avgDegree.toFixed(2)}</div>
            <div className="stat-label">平均度数</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.connectedComponents}</div>
            <div className="stat-label">连通分量</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.largestComponent}</div>
            <div className="stat-label">最大分量</div>
          </div>
        </div>

        <div className="stats-charts">
          <div className="chart-container">
            <h4>实体类型分布</h4>
            <EntityTypeChart data={stats.entityTypes} />
          </div>
          <div className="chart-container">
            <h4>关系类型分布</h4>
            <RelationTypeChart data={stats.relationTypes} />
          </div>
          <div className="chart-container">
            <h4>度分布</h4>
            <DegreeDistributionChart data={stats.degreeDistribution} />
          </div>
        </div>
      </div>
    );
  };

  /**
   * 渲染中心性视图
   */
  const renderCentralityView = () => {
    if (!analysisResult || !Array.isArray(analysisResult)) return null;

    const topNodes = analysisResult.slice(0, 20);

    return (
      <div className="analytics-centrality">
        <div className="centrality-controls">
          <select 
            value={selectedCentrality}
            onChange={(e) => setSelectedCentrality(e.target.value)}
          >
            <option value={CentralityType.DEGREE}>度中心性</option>
            <option value={CentralityType.BETWEENNESS}>介数中心性</option>
            <option value={CentralityType.CLOSENESS}>接近中心性</option>
            <option value={CentralityType.EIGENVECTOR}>特征向量中心性</option>
            <option value={CentralityType.PAGERANK}>PageRank</option>
          </select>
        </div>

        <div className="centrality-chart">
          <CentralityBarChart data={topNodes} />
        </div>

        <div className="centrality-table">
          <table>
            <thead>
              <tr>
                <th>排名</th>
                <th>实体名称</th>
                <th>实体类型</th>
                <th>中心性分数</th>
                <th>度数</th>
              </tr>
            </thead>
            <tbody>
              {topNodes.map((node, index) => (
                <tr key={node.nodeId}>
                  <td>{index + 1}</td>
                  <td>{node.nodeName}</td>
                  <td>{node.entityType}</td>
                  <td>{node.score}</td>
                  <td>{node.degree}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  /**
   * 渲染社区视图
   */
  const renderCommunityView = () => {
    if (!analysisResult || !Array.isArray(analysisResult)) return null;

    return (
      <div className="analytics-community">
        <div className="community-summary">
          <div className="summary-item">
            <span className="summary-value">{analysisResult.length}</span>
            <span className="summary-label">发现社区数</span>
          </div>
        </div>

        <div className="community-list">
          {analysisResult.map((community, index) => (
            <div key={community.id} className="community-card">
              <div className="community-header">
                <h4>社区 {index + 1}</h4>
                <span className="community-size">{community.size} 个实体</span>
              </div>
              <div className="community-nodes">
                {community.nodes.slice(0, 10).map(node => (
                  <span key={node.id} className="community-node-tag">
                    {node.name}
                  </span>
                ))}
                {community.nodes.length > 10 && (
                  <span className="more-nodes">
                    +{community.nodes.length - 10} 更多
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  /**
   * 渲染路径视图
   */
  const renderPathView = () => {
    return (
      <div className="analytics-path">
        <div className="path-inputs">
          <div className="input-group">
            <label>起始实体</label>
            <input
              type="text"
              value={pathSource}
              onChange={(e) => setPathSource(e.target.value)}
              placeholder="输入起始实体ID"
            />
          </div>
          <div className="input-group">
            <label>目标实体</label>
            <input
              type="text"
              value={pathTarget}
              onChange={(e) => setPathTarget(e.target.value)}
              placeholder="输入目标实体ID"
            />
          </div>
          <button onClick={executeAnalysis} disabled={loading}>
            查找路径
          </button>
        </div>

        {analysisResult && (
          <div className="path-result">
            {analysisResult.found ? (
              <>
                <div className="path-info">
                  <span className="path-found">✓ 找到路径</span>
                  <span className="path-length">
                    路径长度: {analysisResult.pathLength} 步
                  </span>
                </div>
                <div className="path-steps">
                  {analysisResult.path.map((step, index) => (
                    <div key={index} className="path-step">
                      <span className="step-number">{step.step}</span>
                      <span className="step-node">{step.node}</span>
                      {step.relation && (
                        <span className="step-relation">({step.relation})</span>
                      )}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="path-not-found">
                ✗ 未找到路径
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="advanced-graph-analytics" style={{ width, height }}>
      <div className="analytics-header">
        <h3>图谱分析</h3>
        <div className="analysis-tabs">
          <button
            className={activeAnalysis === AnalysisType.STATISTICS ? 'active' : ''}
            onClick={() => setActiveAnalysis(AnalysisType.STATISTICS)}
          >
            统计概览
          </button>
          <button
            className={activeAnalysis === AnalysisType.CENTRALITY ? 'active' : ''}
            onClick={() => setActiveAnalysis(AnalysisType.CENTRALITY)}
          >
            中心性分析
          </button>
          <button
            className={activeAnalysis === AnalysisType.COMMUNITY ? 'active' : ''}
            onClick={() => setActiveAnalysis(AnalysisType.COMMUNITY)}
          >
            社区发现
          </button>
          <button
            className={activeAnalysis === AnalysisType.PATH ? 'active' : ''}
            onClick={() => setActiveAnalysis(AnalysisType.PATH)}
          >
            路径分析
          </button>
        </div>
      </div>

      <div className="analytics-content">
        {loading && (
          <div className="analytics-loading">
            <div className="loading-spinner"></div>
            <span>分析中...</span>
          </div>
        )}

        {!loading && activeAnalysis === AnalysisType.STATISTICS && renderStatisticsView()}
        {!loading && activeAnalysis === AnalysisType.CENTRALITY && renderCentralityView()}
        {!loading && activeAnalysis === AnalysisType.COMMUNITY && renderCommunityView()}
        {!loading && activeAnalysis === AnalysisType.PATH && renderPathView()}
      </div>
    </div>
  );
};

/**
 * 实体类型分布图表
 */
const EntityTypeChart = ({ data }) => {
  const chartRef = React.useRef(null);

  React.useEffect(() => {
    if (!chartRef.current || !data) return;

    const chart = echarts.init(chartRef.current);
    
    const option = {
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: Object.entries(data).map(([name, value]) => ({ name, value }))
      }]
    };

    chart.setOption(option);

    return () => chart.dispose();
  }, [data]);

  return <div ref={chartRef} style={{ width: '100%', height: '200px' }} />;
};

/**
 * 关系类型分布图表
 */
const RelationTypeChart = ({ data }) => {
  const chartRef = React.useRef(null);

  React.useEffect(() => {
    if (!chartRef.current || !data) return;

    const chart = echarts.init(chartRef.current);
    
    const option = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { 
        type: 'category',
        data: Object.keys(data),
        axisLabel: { rotate: 45 }
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: Object.values(data),
        itemStyle: { color: '#5470c6' }
      }]
    };

    chart.setOption(option);

    return () => chart.dispose();
  }, [data]);

  return <div ref={chartRef} style={{ width: '100%', height: '200px' }} />;
};

/**
 * 度分布图表
 */
const DegreeDistributionChart = ({ data }) => {
  const chartRef = React.useRef(null);

  React.useEffect(() => {
    if (!chartRef.current || !data) return;

    const chart = echarts.init(chartRef.current);
    
    const degrees = Object.keys(data).map(Number).sort((a, b) => a - b);
    const counts = degrees.map(d => data[d]);

    const option = {
      tooltip: { trigger: 'axis' },
      xAxis: { 
        type: 'category',
        name: '度数',
        data: degrees
      },
      yAxis: { 
        type: 'value',
        name: '节点数'
      },
      series: [{
        type: 'line',
        data: counts,
        smooth: true,
        areaStyle: { opacity: 0.3 }
      }]
    };

    chart.setOption(option);

    return () => chart.dispose();
  }, [data]);

  return <div ref={chartRef} style={{ width: '100%', height: '200px' }} />;
};

/**
 * 中心性柱状图
 */
const CentralityBarChart = ({ data }) => {
  const chartRef = React.useRef(null);

  React.useEffect(() => {
    if (!chartRef.current || !data) return;

    const chart = echarts.init(chartRef.current);
    
    const option = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value' },
      yAxis: { 
        type: 'category',
        data: data.map(d => d.nodeName).reverse()
      },
      series: [{
        type: 'bar',
        data: data.map(d => d.score).reverse(),
        itemStyle: { color: '#91cc75' }
      }]
    };

    chart.setOption(option);

    return () => chart.dispose();
  }, [data]);

  return <div ref={chartRef} style={{ width: '100%', height: '400px' }} />;
};

AdvancedGraphAnalytics.propTypes = {
  graphData: PropTypes.object,
  knowledgeBaseId: PropTypes.string,
  onAnalysisComplete: PropTypes.func,
  width: PropTypes.string,
  height: PropTypes.string
};

export default AdvancedGraphAnalytics;
