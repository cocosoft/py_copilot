/**
 * 增强型知识图谱可视化组件
 *
 * 基于ReactFlow增强知识图谱可视化交互
 *
 * 任务编号: Phase2-Week5
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, Button, Badge, Input } from '../../UnifiedComponentLibrary';

/**
 * 自定义节点组件
 * @param {Object} props - 组件属性
 * @param {Object} props.data - 节点数据
 */
const CustomNode = ({ data }) => {
  const [isHovered, setIsHovered] = useState(false);

  const getNodeColor = () => {
    const colors = {
      person: '#3b82f6',
      organization: '#10b981',
      location: '#f59e0b',
      concept: '#8b5cf6',
      event: '#ef4444',
      default: '#6b7280',
    };
    return colors[data.type] || colors.default;
  };

  return (
    <div
      className={`custom-node ${data.type} ${isHovered ? 'hovered' : ''}`}
      style={{ borderColor: getNodeColor() }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className="node-header"
        style={{ backgroundColor: getNodeColor() }}
      >
        <span className="node-type">{data.type}</span>
        {data.confidence && (
          <span className="node-confidence">
            {(data.confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
      <div className="node-content">
        <div className="node-label">{data.label}</div>
        {data.description && (
          <div className="node-description">{data.description}</div>
        )}
      </div>
      {isHovered && data.properties && (
        <div className="node-tooltip">
          {Object.entries(data.properties).map(([key, value]) => (
            <div key={key} className="tooltip-item">
              <span className="tooltip-key">{key}:</span>
              <span className="tooltip-value">{value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * 图控制面板组件
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 * @param {Function} props.onFilterChange - 过滤变更回调
 * @param {Function} props.onLayoutChange - 布局变更回调
 * @param {Function} props.onExport - 导出回调
 */
const GraphControlPanel = ({
  graphData,
  onFilterChange,
  onLayoutChange,
  onExport,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);

  const nodeTypes = [...new Set(graphData.nodes?.map((n) => n.type) || [])];

  const handleTypeToggle = (type) => {
    const newTypes = selectedTypes.includes(type)
      ? selectedTypes.filter((t) => t !== type)
      : [...selectedTypes, type];
    setSelectedTypes(newTypes);
    onFilterChange?.({ types: newTypes, searchTerm, confidenceThreshold });
  };

  const handleSearch = (value) => {
    setSearchTerm(value);
    onFilterChange?.({ types: selectedTypes, searchTerm: value, confidenceThreshold });
  };

  return (
    <Card className="graph-control-panel">
      <div className="control-section">
        <h4>搜索节点</h4>
        <Input
          placeholder="输入节点名称..."
          value={searchTerm}
          onChange={(e) => handleSearch(e.target.value)}
          prefix={<span>🔍</span>}
        />
      </div>

      <div className="control-section">
        <h4>节点类型过滤</h4>
        <div className="type-filters">
          {nodeTypes.map((type) => (
            <label key={type} className="filter-checkbox">
              <input
                type="checkbox"
                checked={selectedTypes.includes(type)}
                onChange={() => handleTypeToggle(type)}
              />
              <span className="checkbox-label">{type}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="control-section">
        <h4>置信度阈值</h4>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={confidenceThreshold}
          onChange={(e) => {
            const value = parseFloat(e.target.value);
            setConfidenceThreshold(value);
            onFilterChange?.({
              types: selectedTypes,
              searchTerm,
              confidenceThreshold: value,
            });
          }}
        />
        <span className="threshold-value">{(confidenceThreshold * 100).toFixed(0)}%</span>
      </div>

      <div className="control-section">
        <h4>布局选项</h4>
        <div className="layout-buttons">
          <Button size="sm" variant="outline" onClick={() => onLayoutChange?.('force')}>
            力导向
          </Button>
          <Button size="sm" variant="outline" onClick={() => onLayoutChange?.('hierarchical')}>
            层次
          </Button>
          <Button size="sm" variant="outline" onClick={() => onLayoutChange?.('circular')}>
            环形
          </Button>
        </div>
      </div>

      <div className="control-section">
        <h4>导出</h4>
        <div className="export-buttons">
          <Button size="sm" variant="outline" onClick={() => onExport?.('png')}>
            导出PNG
          </Button>
          <Button size="sm" variant="outline" onClick={() => onExport?.('json')}>
            导出JSON
          </Button>
        </div>
      </div>
    </Card>
  );
};

/**
 * 图统计信息组件
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 */
const GraphStatistics = ({ graphData }) => {
  const stats = {
    nodes: graphData.nodes?.length || 0,
    edges: graphData.edges?.length || 0,
    types: new Set(graphData.nodes?.map((n) => n.type)).size,
    avgDegree: graphData.nodes?.length
      ? ((graphData.edges?.length || 0) * 2 / graphData.nodes.length).toFixed(2)
      : 0,
  };

  return (
    <Card className="graph-statistics">
      <div className="stat-item">
        <span className="stat-value">{stats.nodes}</span>
        <span className="stat-label">节点</span>
      </div>
      <div className="stat-item">
        <span className="stat-value">{stats.edges}</span>
        <span className="stat-label">关系</span>
      </div>
      <div className="stat-item">
        <span className="stat-value">{stats.types}</span>
        <span className="stat-label">类型</span>
      </div>
      <div className="stat-item">
        <span className="stat-value">{stats.avgDegree}</span>
        <span className="stat-label">平均度</span>
      </div>
    </Card>
  );
};

/**
 * 增强型知识图谱可视化组件
 * @param {Object} props - 组件属性
 * @param {Object} props.graphData - 图谱数据
 * @param {Function} props.onNodeClick - 节点点击回调
 * @param {Function} props.onEdgeClick - 边点击回调
 * @param {boolean} props.showControls - 是否显示控制面板
 * @param {boolean} props.showStatistics - 是否显示统计信息
 */
const EnhancedGraphVisualization = ({
  graphData = { nodes: [], edges: [] },
  onNodeClick,
  onEdgeClick,
  showControls = true,
  showStatistics = true,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [filteredData, setFilteredData] = useState(graphData);
  const reactFlowInstance = useReactFlow();

  const nodeTypes = {
    custom: CustomNode,
  };

  // 转换数据为ReactFlow格式
  useEffect(() => {
    const flowNodes = filteredData.nodes?.map((node) => ({
      id: node.id,
      type: 'custom',
      position: node.position || { x: Math.random() * 800, y: Math.random() * 600 },
      data: node,
    })) || [];

    const flowEdges = filteredData.edges?.map((edge) => ({
      id: edge.id || `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: 'smoothstep',
      animated: edge.animated || false,
      style: { stroke: edge.color || '#999' },
    })) || [];

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [filteredData, setNodes, setEdges]);

  // 处理过滤
  const handleFilterChange = useCallback(
    (filters) => {
      let filtered = { ...graphData };

      if (filters.types?.length > 0) {
        filtered.nodes = filtered.nodes?.filter((n) =>
          filters.types.includes(n.type)
        );
      }

      if (filters.searchTerm) {
        const term = filters.searchTerm.toLowerCase();
        filtered.nodes = filtered.nodes?.filter(
          (n) =>
            n.label?.toLowerCase().includes(term) ||
            n.description?.toLowerCase().includes(term)
        );
      }

      if (filters.confidenceThreshold > 0) {
        filtered.nodes = filtered.nodes?.filter(
          (n) => (n.confidence || 1) >= filters.confidenceThreshold
        );
      }

      // 过滤边，只保留两端节点都存在的边
      const nodeIds = new Set(filtered.nodes?.map((n) => n.id));
      filtered.edges = graphData.edges?.filter(
        (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
      );

      setFilteredData(filtered);
    },
    [graphData]
  );

  // 处理布局变更
  const handleLayoutChange = useCallback(
    (layoutType) => {
      // 这里可以实现不同的布局算法
      console.log('切换布局:', layoutType);

      // 简单的布局示例
      const newNodes = nodes.map((node, index) => {
        let position = node.position;

        if (layoutType === 'circular') {
          const angle = (index / nodes.length) * 2 * Math.PI;
          const radius = 300;
          position = {
            x: 400 + radius * Math.cos(angle),
            y: 300 + radius * Math.sin(angle),
          };
        } else if (layoutType === 'hierarchical') {
          const level = node.data.level || 0;
          const siblings = nodes.filter(
            (n) => (n.data.level || 0) === level
          );
          const siblingIndex = siblings.indexOf(node);
          position = {
            x: siblingIndex * 200 + 100,
            y: level * 150 + 100,
          };
        }

        return { ...node, position };
      });

      setNodes(newNodes);
      reactFlowInstance.fitView();
    },
    [nodes, setNodes, reactFlowInstance]
  );

  // 处理导出
  const handleExport = useCallback(
    (format) => {
      if (format === 'json') {
        const dataStr = JSON.stringify(filteredData, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'knowledge-graph.json';
        link.click();
      } else if (format === 'png') {
        // 导出PNG需要额外的实现
        console.log('导出PNG功能待实现');
      }
    },
    [filteredData]
  );

  // 处理节点点击
  const handleNodeClick = useCallback(
    (event, node) => {
      onNodeClick?.(node.data);
    },
    [onNodeClick]
  );

  // 处理边点击
  const handleEdgeClick = useCallback(
    (event, edge) => {
      onEdgeClick?.(edge);
    },
    [onEdgeClick]
  );

  return (
    <div className="enhanced-graph-visualization">
      <div className="graph-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          onEdgeClick={handleEdgeClick}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls />
          <MiniMap
            nodeStrokeColor={(n) => {
              if (n.type === 'custom') return '#3b82f6';
              return '#eee';
            }}
            nodeColor={(n) => {
              if (n.type === 'custom') return '#fff';
              return '#eee';
            }}
          />
          <Background variant="dots" gap={12} size={1} />

          {showControls && (
            <Panel position="top-right">
              <GraphControlPanel
                graphData={graphData}
                onFilterChange={handleFilterChange}
                onLayoutChange={handleLayoutChange}
                onExport={handleExport}
              />
            </Panel>
          )}

          {showStatistics && (
            <Panel position="bottom-left">
              <GraphStatistics graphData={filteredData} />
            </Panel>
          )}
        </ReactFlow>
      </div>
    </div>
  );
};

/**
 * 包装组件，提供ReactFlow上下文
 */
const EnhancedGraphVisualizationWrapper = (props) => {
  return (
    <ReactFlowProvider>
      <EnhancedGraphVisualization {...props} />
    </ReactFlowProvider>
  );
};

export default EnhancedGraphVisualizationWrapper;
export { EnhancedGraphVisualization, GraphControlPanel, GraphStatistics };
