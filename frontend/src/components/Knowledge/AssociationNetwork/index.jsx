/**
 * 关联网络可视化组件 - FE-010 关联网络可视化
 *
 * 提供网络图展示、关联类型筛选、关联强度展示、节点详情弹窗功能
 *
 * @task FE-010
 * @phase 前端功能拓展
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Network,
  Filter,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Info,
  X,
  Download,
  Eye,
  EyeOff,
  Layers,
  GitBranch,
  Share2,
  Target,
} from '../icons.jsx';
import './AssociationNetwork.css';

/**
 * 节点数据结构
 * @typedef {Object} Node
 * @property {string} id - 节点ID
 * @property {string} label - 节点标签
 * @property {string} type - 节点类型
 * @property {number} x - X坐标
 * @property {number} y - Y坐标
 * @property {number} size - 节点大小
 */

/**
 * 连线数据结构
 * @typedef {Object} Link
 * @property {string} id - 连线ID
 * @property {string} source - 源节点ID
 * @property {string} target - 目标节点ID
 * @property {string} type - 关联类型
 * @property {number} strength - 关联强度
 */

/**
 * 生成模拟网络数据
 *
 * @param {number} nodeCount - 节点数量
 * @param {number} linkCount - 连线数量
 * @returns {Object} 网络数据
 */
const generateMockNetwork = (nodeCount = 30, linkCount = 50) => {
  const nodeTypes = ['DOCUMENT', 'CHUNK', 'ENTITY', 'CONCEPT'];
  const associationTypes = ['CONTAINS', 'REFERENCES', 'SIMILAR_TO', 'RELATED_TO', 'PART_OF'];
  const nodes = [];
  const links = [];

  // 生成节点
  for (let i = 0; i < nodeCount; i++) {
    nodes.push({
      id: `node-${i}`,
      label: `节点 ${i + 1}`,
      type: nodeTypes[Math.floor(Math.random() * nodeTypes.length)],
      x: Math.random() * 800,
      y: Math.random() * 600,
      size: 20 + Math.random() * 20,
      metadata: {
        description: `这是节点 ${i + 1} 的描述信息`,
        quality: Math.random() * 100,
        createdAt: new Date(Date.now() - Math.random() * 86400000 * 30).toISOString(),
      },
    });
  }

  // 生成连线
  for (let i = 0; i < linkCount; i++) {
    const sourceIdx = Math.floor(Math.random() * nodeCount);
    let targetIdx = Math.floor(Math.random() * nodeCount);
    while (targetIdx === sourceIdx) {
      targetIdx = Math.floor(Math.random() * nodeCount);
    }

    links.push({
      id: `link-${i}`,
      source: nodes[sourceIdx].id,
      target: nodes[targetIdx].id,
      type: associationTypes[Math.floor(Math.random() * associationTypes.length)],
      strength: 0.3 + Math.random() * 0.7,
    });
  }

  return { nodes, links };
};

/**
 * 力导向布局计算
 *
 * @param {Node[]} nodes - 节点数组
 * @param {Link[]} links - 连线数组
 * @param {number} iterations - 迭代次数
 * @returns {Node[]} 计算后的节点位置
 */
const calculateForceLayout = (nodes, links, iterations = 100) => {
  const width = 800;
  const height = 600;
  const centerX = width / 2;
  const centerY = height / 2;

  // 初始化位置
  const positions = nodes.map((node) => ({
    ...node,
    x: node.x || centerX + (Math.random() - 0.5) * 200,
    y: node.y || centerY + (Math.random() - 0.5) * 200,
    vx: 0,
    vy: 0,
  }));

  const nodeMap = new Map(positions.map((n) => [n.id, n]));

  for (let i = 0; i < iterations; i++) {
    // 斥力
    for (let j = 0; j < positions.length; j++) {
      for (let k = j + 1; k < positions.length; k++) {
        const nodeA = positions[j];
        const nodeB = positions[k];
        const dx = nodeB.x - nodeA.x;
        const dy = nodeB.y - nodeA.y;
        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = 5000 / (distance * distance);

        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;

        nodeA.vx -= fx;
        nodeA.vy -= fy;
        nodeB.vx += fx;
        nodeB.vy += fy;
      }
    }

    // 引力
    links.forEach((link) => {
      const source = nodeMap.get(link.source);
      const target = nodeMap.get(link.target);
      if (!source || !target) return;

      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (distance - 100) * 0.01 * link.strength;

      const fx = (dx / distance) * force;
      const fy = (dy / distance) * force;

      source.vx += fx;
      source.vy += fy;
      target.vx -= fx;
      target.vy -= fy;
    });

    // 中心引力
    positions.forEach((node) => {
      const dx = centerX - node.x;
      const dy = centerY - node.y;
      node.vx += dx * 0.001;
      node.vy += dy * 0.001;
    });

    // 更新位置
    positions.forEach((node) => {
      node.vx *= 0.9; // 阻尼
      node.vy *= 0.9;
      node.x += node.vx;
      node.y += node.vy;

      // 边界限制
      node.x = Math.max(50, Math.min(width - 50, node.x));
      node.y = Math.max(50, Math.min(height - 50, node.y));
    });
  }

  return positions;
};

/**
 * 获取节点类型颜色
 *
 * @param {string} type - 节点类型
 * @returns {string} 颜色代码
 */
const getNodeColor = (type) => {
  const colors = {
    DOCUMENT: '#1890ff',
    CHUNK: '#52c41a',
    ENTITY: '#faad14',
    CONCEPT: '#eb2f96',
    RELATIONSHIP: '#722ed1',
  };
  return colors[type] || '#8c8c8c';
};

/**
 * 获取关联类型标签
 *
 * @param {string} type - 关联类型
 * @returns {string} 标签文本
 */
const getAssociationLabel = (type) => {
  const labels = {
    CONTAINS: '包含',
    REFERENCES: '引用',
    SIMILAR_TO: '相似',
    RELATED_TO: '相关',
    PART_OF: '属于',
    INSTANCE_OF: '实例',
    SUBCLASS_OF: '子类',
    MENTIONS: '提及',
  };
  return labels[type] || type;
};

/**
 * 节点详情弹窗组件
 */
const NodeDetailPopup = ({ node, onClose, associations }) => {
  if (!node) return null;

  const relatedLinks = associations.filter(
    (link) => link.source === node.id || link.target === node.id
  );

  return (
    <div className="node-detail-popup">
      <div className="popup-header">
        <h4>{node.label}</h4>
        <button className="close-btn" onClick={onClose}>
          <X size={16} />
        </button>
      </div>

      <div className="popup-content">
        <div className="detail-section">
          <div className="detail-row">
            <span className="detail-label">类型</span>
            <span
              className="detail-value type-badge"
              style={{ background: getNodeColor(node.type) + '20', color: getNodeColor(node.type) }}
            >
              {node.type}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">ID</span>
            <span className="detail-value">{node.id}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">质量分数</span>
            <span className="detail-value">{node.metadata.quality.toFixed(1)}</span>
          </div>
        </div>

        <div className="detail-section">
          <h5>描述</h5>
          <p className="detail-description">{node.metadata.description}</p>
        </div>

        <div className="detail-section">
          <h5>关联关系 ({relatedLinks.length})</h5>
          <div className="related-links">
            {relatedLinks.map((link) => (
              <div key={link.id} className="related-link-item">
                <span className="link-type">{getAssociationLabel(link.type)}</span>
                <div className="strength-bar">
                  <div
                    className="strength-fill"
                    style={{ width: `${link.strength * 100}%` }}
                  />
                </div>
                <span className="strength-value">{(link.strength * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 关联网络可视化组件
 */
const AssociationNetwork = ({
  nodes: initialNodes,
  links: initialLinks,
  width = 800,
  height = 600,
  onNodeClick,
  onNodeHover,
}) => {
  const svgRef = useRef(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [showLabels, setShowLabels] = useState(true);
  const [activeFilters, setActiveFilters] = useState(new Set());
  const [showDetailPopup, setShowDetailPopup] = useState(false);

  // 初始化数据 - 使用真实数据，如果没有则返回空数组
  const { nodes, links } = useMemo(() => {
    return { 
      nodes: initialNodes || [], 
      links: initialLinks || [] 
    };
  }, [initialNodes, initialLinks]);

  // 计算布局
  const layoutNodes = useMemo(() => {
    return calculateForceLayout(nodes, links, 100);
  }, [nodes, links]);

  // 过滤后的连线
  const filteredLinks = useMemo(() => {
    if (activeFilters.size === 0) return links;
    return links.filter((link) => activeFilters.has(link.type));
  }, [links, activeFilters]);

  // 获取所有关联类型
  const associationTypes = useMemo(() => {
    const types = new Set(links.map((link) => link.type));
    return Array.from(types);
  }, [links]);

  // 处理缩放
  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.2, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.2, 0.5));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // 处理拖拽
  const handleMouseDown = (e) => {
    if (e.target.tagName === 'svg') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // 处理节点点击
  const handleNodeClick = (node) => {
    setSelectedNode(node);
    setShowDetailPopup(true);
    onNodeClick?.(node);
  };

  // 处理节点悬停
  const handleNodeHover = (node) => {
    setHoveredNode(node);
    onNodeHover?.(node);
  };

  // 切换过滤器
  const toggleFilter = (type) => {
    setActiveFilters((prev) => {
      const newFilters = new Set(prev);
      if (newFilters.has(type)) {
        newFilters.delete(type);
      } else {
        newFilters.add(type);
      }
      return newFilters;
    });
  };

  // 导出网络图
  const handleExport = () => {
    const svgElement = svgRef.current;
    if (!svgElement) return;

    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    canvas.width = width;
    canvas.height = height;

    img.onload = () => {
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);

      const link = document.createElement('a');
      link.download = `association-network-${Date.now()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  };

  // 统计信息
  const stats = useMemo(() => {
    const nodeTypes = {};
    nodes.forEach((node) => {
      nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;
    });

    const linkTypes = {};
    filteredLinks.forEach((link) => {
      linkTypes[link.type] = (linkTypes[link.type] || 0) + 1;
    });

    return {
      nodeCount: nodes.length,
      linkCount: filteredLinks.length,
      nodeTypes,
      linkTypes,
    };
  }, [nodes, filteredLinks]);

  return (
    <div className="association-network">
      {/* 工具栏 */}
      <div className="network-toolbar">
        <div className="toolbar-left">
          <h3>关联网络</h3>
          <span className="stats-badge">
            {stats.nodeCount} 节点 | {stats.linkCount} 关联
          </span>
        </div>

        <div className="toolbar-right">
          {/* 显示标签开关 */}
          <button
            className={`toolbar-btn ${showLabels ? 'active' : ''}`}
            onClick={() => setShowLabels(!showLabels)}
            title={showLabels ? '隐藏标签' : '显示标签'}
          >
            {showLabels ? <Eye size={16} /> : <EyeOff size={16} />}
          </button>

          {/* 缩放控制 */}
          <button className="toolbar-btn" onClick={handleZoomIn} title="放大">
            <ZoomIn size={16} />
          </button>
          <button className="toolbar-btn" onClick={handleZoomOut} title="缩小">
            <ZoomOut size={16} />
          </button>
          <button className="toolbar-btn" onClick={handleReset} title="重置">
            <RotateCcw size={16} />
          </button>

          {/* 导出 */}
          <button className="toolbar-btn" onClick={handleExport} title="导出">
            <Download size={16} />
          </button>
        </div>
      </div>

      {/* 过滤器 */}
      <div className="network-filters">
        <div className="filter-header">
          <Filter size={14} />
          <span>关联类型筛选</span>
        </div>
        <div className="filter-tags">
          {associationTypes.map((type) => (
            <button
              key={type}
              className={`filter-tag ${activeFilters.has(type) ? 'active' : ''}`}
              onClick={() => toggleFilter(type)}
            >
              {getAssociationLabel(type)}
              <span className="filter-count">
                {links.filter((l) => l.type === type).length}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 网络图 */}
      <div className="network-container">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          <defs>
            {/* 箭头标记 */}
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="28"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#d9d9d9" />
            </marker>
          </defs>

          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
            {/* 连线 */}
            {filteredLinks.map((link) => {
              const source = layoutNodes.find((n) => n.id === link.source);
              const target = layoutNodes.find((n) => n.id === link.target);
              if (!source || !target) return null;

              const isHighlighted =
                hoveredNode &&
                (link.source === hoveredNode.id || link.target === hoveredNode.id);

              return (
                <g key={link.id}>
                  <line
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke={isHighlighted ? '#1890ff' : '#d9d9d9'}
                    strokeWidth={isHighlighted ? 3 : 1 + link.strength * 2}
                    opacity={isHighlighted ? 1 : 0.6}
                    markerEnd="url(#arrowhead)"
                  />
                  {/* 关联类型标签 */}
                  {showLabels && (
                    <text
                      x={(source.x + target.x) / 2}
                      y={(source.y + target.y) / 2}
                      textAnchor="middle"
                      fontSize={10}
                      fill={isHighlighted ? '#1890ff' : '#8c8c8c'}
                      className="link-label"
                    >
                      {getAssociationLabel(link.type)}
                    </text>
                  )}
                </g>
              );
            })}

            {/* 节点 */}
            {layoutNodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const isHovered = hoveredNode?.id === node.id;
              const isRelated =
                hoveredNode &&
                filteredLinks.some(
                  (link) =>
                    (link.source === hoveredNode.id && link.target === node.id) ||
                    (link.target === hoveredNode.id && link.source === node.id)
                );

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={() => handleNodeClick(node)}
                  onMouseEnter={() => handleNodeHover(node)}
                  onMouseLeave={() => handleNodeHover(null)}
                  style={{ cursor: 'pointer' }}
                  className={`network-node ${isSelected ? 'selected' : ''} ${
                    isHovered ? 'hovered' : ''
                  } ${isRelated ? 'related' : ''}`}
                >
                  <circle
                    r={node.size / 2}
                    fill={getNodeColor(node.type)}
                    stroke={isSelected ? '#1890ff' : '#fff'}
                    strokeWidth={isSelected ? 3 : 2}
                    opacity={hoveredNode && !isHovered && !isRelated ? 0.3 : 1}
                  />
                  {showLabels && (
                    <text
                      y={node.size / 2 + 15}
                      textAnchor="middle"
                      fontSize={11}
                      fill="#262626"
                      opacity={hoveredNode && !isHovered && !isRelated ? 0.3 : 1}
                    >
                      {node.label}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>

        {/* 图例 */}
        <div className="network-legend">
          <h5>节点类型</h5>
          {Object.entries(stats.nodeTypes).map(([type, count]) => (
            <div key={type} className="legend-item">
              <span
                className="legend-dot"
                style={{ background: getNodeColor(type) }}
              />
              <span className="legend-label">{type}</span>
              <span className="legend-count">{count}</span>
            </div>
          ))}
        </div>

        {/* 详情弹窗 */}
        {showDetailPopup && (
          <NodeDetailPopup
            node={selectedNode}
            onClose={() => setShowDetailPopup(false)}
            associations={filteredLinks}
          />
        )}
      </div>

      {/* 统计面板 */}
      <div className="network-stats">
        <div className="stats-row">
          <div className="stat-item">
            <Layers size={16} />
            <span>{stats.nodeCount} 节点</span>
          </div>
          <div className="stat-item">
            <GitBranch size={16} />
            <span>{stats.linkCount} 关联</span>
          </div>
          <div className="stat-item">
            <Share2 size={16} />
            <span>
              {stats.linkCount > 0
                ? (stats.linkCount / stats.nodeCount).toFixed(2)
                : 0}{' '}
              平均度数
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 带控制面板的关联网络
 */
export const AssociationNetworkWithControls = (props) => {
  const [showControls, setShowControls] = useState(true);

  return (
    <div className="association-network-wrapper">
      <AssociationNetwork {...props} />

      <button
        className="controls-toggle"
        onClick={() => setShowControls(!showControls)}
      >
        {showControls ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
      </button>
    </div>
  );
};

export default AssociationNetwork;
