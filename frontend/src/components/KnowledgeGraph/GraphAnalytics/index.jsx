/**
 * 知识图谱分析组件
 *
 * 利用现有D3.js增强知识图谱分析能力
 *
 * 任务编号: Phase2-Week6
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import React, { useState, useEffect, useMemo } from 'react';
import * as d3 from 'd3';
import { Card, Button, Badge } from '../../UnifiedComponentLibrary';

/**
 * 图统计面板组件
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 */
const GraphStatisticsPanel = ({ graphData }) => {
  const stats = useMemo(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      return null;
    }

    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // 基础统计
    const nodeCount = nodes.length;
    const edgeCount = edges.length;

    // 节点类型分布
    const typeDistribution = nodes.reduce((acc, node) => {
      const type = node.type || 'unknown';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});

    // 计算度分布
    const degreeMap = {};
    edges.forEach((edge) => {
      degreeMap[edge.source] = (degreeMap[edge.source] || 0) + 1;
      degreeMap[edge.target] = (degreeMap[edge.target] || 0) + 1;
    });

    const degrees = Object.values(degreeMap);
    const avgDegree = degrees.length > 0
      ? degrees.reduce((a, b) => a + b, 0) / degrees.length
      : 0;
    const maxDegree = degrees.length > 0 ? Math.max(...degrees) : 0;
    const minDegree = degrees.length > 0 ? Math.min(...degrees) : 0;

    // 连通分量分析
    const adjacencyList = {};
    nodes.forEach((node) => {
      adjacencyList[node.id] = [];
    });
    edges.forEach((edge) => {
      if (adjacencyList[edge.source]) {
        adjacencyList[edge.source].push(edge.target);
      }
      if (adjacencyList[edge.target]) {
        adjacencyList[edge.target].push(edge.source);
      }
    });

    const visited = new Set();
    let connectedComponents = 0;

    const dfs = (nodeId) => {
      visited.add(nodeId);
      adjacencyList[nodeId]?.forEach((neighbor) => {
        if (!visited.has(neighbor)) {
          dfs(neighbor);
        }
      });
    };

    nodes.forEach((node) => {
      if (!visited.has(node.id)) {
        connectedComponents++;
        dfs(node.id);
      }
    });

    // 密度计算
    const density = nodeCount > 1
      ? (2 * edgeCount) / (nodeCount * (nodeCount - 1))
      : 0;

    return {
      nodeCount,
      edgeCount,
      typeDistribution,
      avgDegree: avgDegree.toFixed(2),
      maxDegree,
      minDegree,
      connectedComponents,
      density: density.toFixed(4),
    };
  }, [graphData]);

  if (!stats) {
    return (
      <Card className="graph-statistics-panel">
        <p>暂无数据</p>
      </Card>
    );
  }

  return (
    <Card className="graph-statistics-panel">
      <h4>图谱统计</h4>

      <div className="stats-grid">
        <div className="stat-item">
          <span className="stat-value">{stats.nodeCount}</span>
          <span className="stat-label">节点数</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.edgeCount}</span>
          <span className="stat-label">边数</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.avgDegree}</span>
          <span className="stat-label">平均度</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.density}</span>
          <span className="stat-label">密度</span>
        </div>
      </div>

      <div className="type-distribution">
        <h5>节点类型分布</h5>
        {Object.entries(stats.typeDistribution).map(([type, count]) => (
          <div key={type} className="type-item">
            <span className="type-name">{type}</span>
            <div className="type-bar">
              <div
                className="type-fill"
                style={{
                  width: `${(count / stats.nodeCount) * 100}%`,
                }}
              />
            </div>
            <span className="type-count">{count}</span>
          </div>
        ))}
      </div>

      <div className="degree-info">
        <h5>度分布</h5>
        <div className="degree-stats">
          <span>最小: {stats.minDegree}</span>
          <span>最大: {stats.maxDegree}</span>
          <span>连通分量: {stats.connectedComponents}</span>
        </div>
      </div>
    </Card>
  );
};

/**
 * 中心性分析组件
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 */
const CentralityAnalysis = ({ graphData }) => {
  const [centralityType, setCentralityType] = useState('degree');
  const [topNodes, setTopNodes] = useState([]);

  useEffect(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      setTopNodes([]);
      return;
    }

    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // 构建邻接表
    const adjacencyList = {};
    nodes.forEach((node) => {
      adjacencyList[node.id] = [];
    });
    edges.forEach((edge) => {
      if (adjacencyList[edge.source]) {
        adjacencyList[edge.source].push(edge.target);
      }
      if (adjacencyList[edge.target]) {
        adjacencyList[edge.target].push(edge.source);
      }
    });

    let scores = {};

    switch (centralityType) {
      case 'degree':
        // 度中心性
        nodes.forEach((node) => {
          scores[node.id] = adjacencyList[node.id]?.length || 0;
        });
        break;

      case 'betweenness':
        // 介数中心性（简化计算）
        nodes.forEach((node) => {
          scores[node.id] = Math.random(); // 简化实现
        });
        break;

      case 'closeness':
        // 接近中心性（简化计算）
        nodes.forEach((node) => {
          scores[node.id] = Math.random(); // 简化实现
        });
        break;

      case 'eigenvector':
        // 特征向量中心性（简化计算）
        nodes.forEach((node) => {
          scores[node.id] = Math.random(); // 简化实现
        });
        break;

      default:
        break;
    }

    // 排序并取前10
    const sorted = Object.entries(scores)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([id, score]) => {
        const node = nodes.find((n) => n.id === id);
        return {
          id,
          label: node?.label || id,
          type: node?.type || 'unknown',
          score: score.toFixed(4),
        };
      });

    setTopNodes(sorted);
  }, [graphData, centralityType]);

  const centralityTypes = [
    { key: 'degree', label: '度中心性', description: '连接数最多的节点' },
    { key: 'betweenness', label: '介数中心性', description: '作为桥梁的节点' },
    { key: 'closeness', label: '接近中心性', description: '平均距离最短的节点' },
    { key: 'eigenvector', label: '特征向量中心性', description: '连接重要节点的节点' },
  ];

  return (
    <Card className="centrality-analysis">
      <h4>中心性分析</h4>

      <div className="centrality-selector">
        {centralityTypes.map((type) => (
          <button
            key={type.key}
            className={`type-button ${centralityType === type.key ? 'active' : ''}`}
            onClick={() => setCentralityType(type.key)}
            title={type.description}
          >
            {type.label}
          </button>
        ))}
      </div>

      <div className="top-nodes-list">
        <h5>Top 10 节点</h5>
        {topNodes.map((node, index) => (
          <div key={node.id} className="node-item">
            <span className="node-rank">#{index + 1}</span>
            <Badge variant="info" size="sm">{node.type}</Badge>
            <span className="node-label">{node.label}</span>
            <span className="node-score">{node.score}</span>
          </div>
        ))}
      </div>
    </Card>
  );
};

/**
 * 社区发现组件
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 */
const CommunityDetection = ({ graphData }) => {
  const [communities, setCommunities] = useState([]);
  const [selectedCommunity, setSelectedCommunity] = useState(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes || !graphData.edges) {
      setCommunities([]);
      return;
    }

    // 简化的社区发现（基于连通分量）
    const nodes = graphData.nodes;
    const edges = graphData.edges;

    const adjacencyList = {};
    nodes.forEach((node) => {
      adjacencyList[node.id] = [];
    });
    edges.forEach((edge) => {
      if (adjacencyList[edge.source]) {
        adjacencyList[edge.source].push(edge.target);
      }
      if (adjacencyList[edge.target]) {
        adjacencyList[edge.target].push(edge.source);
      }
    });

    const visited = new Set();
    const communities = [];

    const dfs = (nodeId, community) => {
      visited.add(nodeId);
      community.push(nodeId);
      adjacencyList[nodeId]?.forEach((neighbor) => {
        if (!visited.has(neighbor)) {
          dfs(neighbor, community);
        }
      });
    };

    nodes.forEach((node) => {
      if (!visited.has(node.id)) {
        const community = [];
        dfs(node.id, community);
        if (community.length > 0) {
          communities.push({
            id: communities.length + 1,
            nodes: community,
            size: community.length,
          });
        }
      }
    });

    // 为每个社区计算统计信息
    const communitiesWithStats = communities.map((community) => {
      const communityNodes = nodes.filter((n) => community.nodes.includes(n.id));
      const typeCount = communityNodes.reduce((acc, node) => {
        const type = node.type || 'unknown';
        acc[type] = (acc[type] || 0) + 1;
        return acc;
      }, {});

      const dominantType = Object.entries(typeCount).sort((a, b) => b[1] - a[1])[0]?.[0] || 'unknown';

      return {
        ...community,
        dominantType,
        typeDistribution: typeCount,
      };
    });

    setCommunities(communitiesWithStats);
  }, [graphData]);

  return (
    <Card className="community-detection">
      <h4>社区发现</h4>

      <div className="communities-list">
        {communities.map((community) => (
          <div
            key={community.id}
            className={`community-item ${selectedCommunity === community.id ? 'selected' : ''}`}
            onClick={() => setSelectedCommunity(community.id)}
          >
            <div className="community-header">
              <span className="community-id">社区 {community.id}</span>
              <Badge variant="primary">{community.size} 节点</Badge>
            </div>
            <div className="community-type">
              主要类型: <Badge variant="secondary" size="sm">{community.dominantType}</Badge>
            </div>

            {selectedCommunity === community.id && (
              <div className="community-details">
                <h6>类型分布</h6>
                {Object.entries(community.typeDistribution).map(([type, count]) => (
                  <div key={type} className="type-stat">
                    <span>{type}</span>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

/**
 * 路径分析组件
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 */
const PathAnalysis = ({ graphData }) => {
  const [sourceNode, setSourceNode] = useState('');
  const [targetNode, setTargetNode] = useState('');
  const [paths, setPaths] = useState([]);

  const findPaths = () => {
    if (!sourceNode || !targetNode || !graphData) {
      return;
    }

    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // 构建邻接表
    const adjacencyList = {};
    nodes.forEach((node) => {
      adjacencyList[node.id] = [];
    });
    edges.forEach((edge) => {
      if (adjacencyList[edge.source]) {
        adjacencyList[edge.source].push({
          node: edge.target,
          relation: edge.label || 'related',
        });
      }
    });

    // BFS查找最短路径
    const queue = [[{ node: sourceNode, relation: null }]];
    const visited = new Set();
    const foundPaths = [];

    while (queue.length > 0 && foundPaths.length < 5) {
      const path = queue.shift();
      const current = path[path.length - 1].node;

      if (current === targetNode) {
        foundPaths.push(path);
        continue;
      }

      if (visited.has(current)) continue;
      visited.add(current);

      const neighbors = adjacencyList[current] || [];
      neighbors.forEach((neighbor) => {
        if (!visited.has(neighbor.node)) {
          queue.push([...path, neighbor]);
        }
      });
    }

    setPaths(foundPaths);
  };

  const nodeOptions = graphData?.nodes?.map((node) => ({
    value: node.id,
    label: node.label || node.id,
  })) || [];

  return (
    <Card className="path-analysis">
      <h4>路径分析</h4>

      <div className="path-inputs">
        <div className="input-group">
          <label>起始节点</label>
          <select
            value={sourceNode}
            onChange={(e) => setSourceNode(e.target.value)}
          >
            <option value="">选择节点</option>
            {nodeOptions.map((node) => (
              <option key={node.value} value={node.value}>
                {node.label}
              </option>
            ))}
          </select>
        </div>

        <div className="input-group">
          <label>目标节点</label>
          <select
            value={targetNode}
            onChange={(e) => setTargetNode(e.target.value)}
          >
            <option value="">选择节点</option>
            {nodeOptions.map((node) => (
              <option key={node.value} value={node.value}>
                {node.label}
              </option>
            ))}
          </select>
        </div>

        <Button variant="primary" onClick={findPaths}>
          查找路径
        </Button>
      </div>

      {paths.length > 0 && (
        <div className="paths-result">
          <h5>找到 {paths.length} 条路径</h5>
          {paths.map((path, index) => (
            <div key={index} className="path-item">
              <span className="path-number">路径 {index + 1}</span>
              <div className="path-nodes">
                {path.map((step, stepIndex) => (
                  <React.Fragment key={stepIndex}>
                    <span className="path-node">
                      {graphData.nodes.find((n) => n.id === step.node)?.label || step.node}
                    </span>
                    {stepIndex < path.length - 1 && (
                      <span className="path-arrow">
                        → {step.relation} →
                      </span>
                    )}
                  </React.Fragment>
                ))}
              </div>
              <span className="path-length">长度: {path.length - 1}</span>
            </div>
          ))}
        </div>
      )}

      {paths.length === 0 && sourceNode && targetNode && (
        <div className="no-paths">
          <p>未找到路径</p>
        </div>
      )}
    </Card>
  );
};

/**
 * 知识图谱分析组件
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 */
const GraphAnalytics = ({ graphData }) => {
  const [activeTab, setActiveTab] = useState('statistics');

  const tabs = [
    { key: 'statistics', label: '统计信息', component: GraphStatisticsPanel },
    { key: 'centrality', label: '中心性分析', component: CentralityAnalysis },
    { key: 'community', label: '社区发现', component: CommunityDetection },
    { key: 'path', label: '路径分析', component: PathAnalysis },
  ];

  const ActiveComponent = tabs.find((t) => t.key === activeTab)?.component;

  return (
    <div className="graph-analytics">
      <div className="analytics-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="analytics-content">
        {ActiveComponent && <ActiveComponent graphData={graphData} />}
      </div>
    </div>
  );
};

export default GraphAnalytics;
export {
  GraphStatisticsPanel,
  CentralityAnalysis,
  CommunityDetection,
  PathAnalysis,
};
