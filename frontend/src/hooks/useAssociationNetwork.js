/**
 * 关联网络可视化 Hooks - FE-010 关联网络可视化
 *
 * 提供关联网络可视化相关的数据获取和操作功能
 *
 * @task FE-010
 * @phase 前端功能拓展
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import apiClient from '../services/apiClient';

/**
 * 使用网络数据
 *
 * @param {Object} options - 配置选项
 * @returns {Object} 网络数据和操作
 */
export const useNetworkData = (options = {}) => {
  const { knowledgeBaseId, depth = 2, enabled = true } = options;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['network', 'data', knowledgeBaseId, depth],
    queryFn: async () => {
      if (!knowledgeBaseId) return null;
      const response = await apiClient.get('/api/v1/knowledge/network', {
        params: { knowledge_base_id: knowledgeBaseId, depth },
      });
      return response.data;
    },
    enabled: !!knowledgeBaseId && enabled,
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  return useMemo(
    () => ({
      nodes: data?.nodes || [],
      links: data?.links || [],
      isLoading,
      error,
      refetch,
    }),
    [data, isLoading, error, refetch]
  );
};

/**
 * 使用力导向布局
 *
 * @param {Array} nodes - 节点数组
 * @param {Array} links - 连线数组
 * @param {Object} options - 配置选项
 * @returns {Object} 布局后的节点位置和控制器
 */
export const useForceLayout = (nodes, links, options = {}) => {
  const {
    width = 800,
    height = 600,
    iterations = 100,
    repulsion = 5000,
    springLength = 100,
    springStrength = 0.01,
    damping = 0.9,
    enabled = true,
  } = options;

  const [positions, setPositions] = useState([]);
  const [isCalculating, setIsCalculating] = useState(false);
  const animationRef = useRef(null);

  // 计算力导向布局
  const calculateLayout = useCallback(() => {
    if (!nodes || nodes.length === 0) return;

    setIsCalculating(true);

    const centerX = width / 2;
    const centerY = height / 2;

    // 初始化位置
    const newPositions = nodes.map((node) => ({
      ...node,
      x: node.x || centerX + (Math.random() - 0.5) * 200,
      y: node.y || centerY + (Math.random() - 0.5) * 200,
      vx: 0,
      vy: 0,
    }));

    const nodeMap = new Map(newPositions.map((n) => [n.id, n]));

    // 力导向算法
    for (let i = 0; i < iterations; i++) {
      // 斥力
      for (let j = 0; j < newPositions.length; j++) {
        for (let k = j + 1; k < newPositions.length; k++) {
          const nodeA = newPositions[j];
          const nodeB = newPositions[k];
          const dx = nodeB.x - nodeA.x;
          const dy = nodeB.y - nodeA.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsion / (distance * distance);

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
        const force = (distance - springLength) * springStrength * (link.strength || 1);

        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;

        source.vx += fx;
        source.vy += fy;
        target.vx -= fx;
        target.vy -= fy;
      });

      // 中心引力
      newPositions.forEach((node) => {
        const dx = centerX - node.x;
        const dy = centerY - node.y;
        node.vx += dx * 0.001;
        node.vy += dy * 0.001;
      });

      // 更新位置
      newPositions.forEach((node) => {
        node.vx *= damping;
        node.vy *= damping;
        node.x += node.vx;
        node.y += node.vy;

        // 边界限制
        node.x = Math.max(50, Math.min(width - 50, node.x));
        node.y = Math.max(50, Math.min(height - 50, node.y));
      });
    }

    setPositions(newPositions);
    setIsCalculating(false);
  }, [nodes, links, width, height, iterations, repulsion, springLength, springStrength, damping]);

  // 重新计算布局
  const recalculate = useCallback(() => {
    calculateLayout();
  }, [calculateLayout]);

  // 初始计算
  useEffect(() => {
    if (enabled && nodes.length > 0) {
      calculateLayout();
    }
  }, [enabled, nodes, links, calculateLayout]);

  return useMemo(
    () => ({
      positions,
      isCalculating,
      recalculate,
    }),
    [positions, isCalculating, recalculate]
  );
};

/**
 * 使用网络视图控制
 *
 * @param {Object} options - 配置选项
 * @returns {Object} 视图控制状态和操作
 */
export const useNetworkView = (options = {}) => {
  const { initialZoom = 1, initialPan = { x: 0, y: 0 } } = options;

  const [zoom, setZoom] = useState(initialZoom);
  const [pan, setPan] = useState(initialPan);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // 缩放操作
  const zoomIn = useCallback(() => {
    setZoom((z) => Math.min(z * 1.2, 5));
  }, []);

  const zoomOut = useCallback(() => {
    setZoom((z) => Math.max(z / 1.2, 0.2));
  }, []);

  const resetView = useCallback(() => {
    setZoom(initialZoom);
    setPan(initialPan);
  }, [initialZoom, initialPan]);

  // 拖拽操作
  const startDrag = useCallback((e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  }, []);

  const drag = useCallback(
    (e) => {
      if (isDragging) {
        const dx = e.clientX - dragStart.x;
        const dy = e.clientY - dragStart.y;
        setPan((p) => ({ x: p.x + dx, y: p.y + dy }));
        setDragStart({ x: e.clientX, y: e.clientY });
      }
    },
    [isDragging, dragStart]
  );

  const endDrag = useCallback(() => {
    setIsDragging(false);
  }, []);

  // 平移到指定位置
  const panTo = useCallback((x, y) => {
    setPan({ x, y });
  }, []);

  // 缩放到指定级别
  const zoomTo = useCallback((level) => {
    setZoom(Math.max(0.2, Math.min(5, level)));
  }, []);

  return useMemo(
    () => ({
      zoom,
      pan,
      isDragging,
      zoomIn,
      zoomOut,
      resetView,
      startDrag,
      drag,
      endDrag,
      panTo,
      zoomTo,
    }),
    [zoom, pan, isDragging, zoomIn, zoomOut, resetView, startDrag, drag, endDrag, panTo, zoomTo]
  );
};

/**
 * 使用节点选择
 *
 * @returns {Object} 节点选择状态和操作
 */
export const useNodeSelection = () => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [selectionHistory, setSelectionHistory] = useState([]);

  const selectNode = useCallback((node) => {
    setSelectedNode(node);
    if (node) {
      setSelectionHistory((prev) => [
        { node, timestamp: Date.now() },
        ...prev.slice(0, 19),
      ]);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const hoverNode = useCallback((node) => {
    setHoveredNode(node);
  }, []);

  const goBack = useCallback(() => {
    if (selectionHistory.length > 1) {
      const previous = selectionHistory[1];
      setSelectedNode(previous.node);
      setSelectionHistory((prev) => prev.slice(1));
    }
  }, [selectionHistory]);

  return useMemo(
    () => ({
      selectedNode,
      hoveredNode,
      selectionHistory,
      selectNode,
      clearSelection,
      hoverNode,
      goBack,
      canGoBack: selectionHistory.length > 1,
    }),
    [selectedNode, hoveredNode, selectionHistory, selectNode, clearSelection, hoverNode, goBack]
  );
};

/**
 * 使用网络过滤器
 *
 * @returns {Object} 过滤器状态和操作
 */
export const useNetworkFilters = () => {
  const [nodeTypeFilter, setNodeTypeFilter] = useState(new Set());
  const [linkTypeFilter, setLinkTypeFilter] = useState(new Set());
  const [minStrength, setMinStrength] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  // 切换节点类型过滤
  const toggleNodeType = useCallback((type) => {
    setNodeTypeFilter((prev) => {
      const newFilter = new Set(prev);
      if (newFilter.has(type)) {
        newFilter.delete(type);
      } else {
        newFilter.add(type);
      }
      return newFilter;
    });
  }, []);

  // 切换连线类型过滤
  const toggleLinkType = useCallback((type) => {
    setLinkTypeFilter((prev) => {
      const newFilter = new Set(prev);
      if (newFilter.has(type)) {
        newFilter.delete(type);
      } else {
        newFilter.add(type);
      }
      return newFilter;
    });
  }, []);

  // 清除所有过滤器
  const clearFilters = useCallback(() => {
    setNodeTypeFilter(new Set());
    setLinkTypeFilter(new Set());
    setMinStrength(0);
    setSearchQuery('');
  }, []);

  // 过滤节点
  const filterNodes = useCallback(
    (nodes) => {
      return nodes.filter((node) => {
        // 类型过滤
        if (nodeTypeFilter.size > 0 && !nodeTypeFilter.has(node.type)) {
          return false;
        }
        // 搜索过滤
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          return (
            node.label.toLowerCase().includes(query) ||
            node.id.toLowerCase().includes(query)
          );
        }
        return true;
      });
    },
    [nodeTypeFilter, searchQuery]
  );

  // 过滤连线
  const filterLinks = useCallback(
    (links) => {
      return links.filter((link) => {
        // 类型过滤
        if (linkTypeFilter.size > 0 && !linkTypeFilter.has(link.type)) {
          return false;
        }
        // 强度过滤
        if (link.strength < minStrength) {
          return false;
        }
        return true;
      });
    },
    [linkTypeFilter, minStrength]
  );

  // 是否有激活的过滤器
  const hasActiveFilters = useMemo(() => {
    return (
      nodeTypeFilter.size > 0 ||
      linkTypeFilter.size > 0 ||
      minStrength > 0 ||
      searchQuery.length > 0
    );
  }, [nodeTypeFilter, linkTypeFilter, minStrength, searchQuery]);

  return useMemo(
    () => ({
      nodeTypeFilter,
      linkTypeFilter,
      minStrength,
      searchQuery,
      toggleNodeType,
      toggleLinkType,
      setMinStrength,
      setSearchQuery,
      clearFilters,
      filterNodes,
      filterLinks,
      hasActiveFilters,
    }),
    [
      nodeTypeFilter,
      linkTypeFilter,
      minStrength,
      searchQuery,
      toggleNodeType,
      toggleLinkType,
      clearFilters,
      filterNodes,
      filterLinks,
      hasActiveFilters,
    ]
  );
};

/**
 * 使用网络统计
 *
 * @param {Array} nodes - 节点数组
 * @param {Array} links - 连线数组
 * @returns {Object} 统计数据
 */
export const useNetworkStats = (nodes, links) => {
  return useMemo(() => {
    if (!nodes || nodes.length === 0) {
      return {
        nodeCount: 0,
        linkCount: 0,
        nodeTypes: {},
        linkTypes: {},
        avgDegree: 0,
        density: 0,
      };
    }

    // 节点类型统计
    const nodeTypes = {};
    nodes.forEach((node) => {
      nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;
    });

    // 连线类型统计
    const linkTypes = {};
    links.forEach((link) => {
      linkTypes[link.type] = (linkTypes[link.type] || 0) + 1;
    });

    // 平均度数
    const avgDegree = nodes.length > 0 ? (links.length * 2) / nodes.length : 0;

    // 网络密度
    const maxLinks = (nodes.length * (nodes.length - 1)) / 2;
    const density = maxLinks > 0 ? links.length / maxLinks : 0;

    return {
      nodeCount: nodes.length,
      linkCount: links.length,
      nodeTypes,
      linkTypes,
      avgDegree: avgDegree.toFixed(2),
      density: density.toFixed(3),
    };
  }, [nodes, links]);
};

/**
 * 使用网络导出
 *
 * @returns {Object} 导出功能
 */
export const useNetworkExport = () => {
  const [isExporting, setIsExporting] = useState(false);

  // 导出为PNG
  const exportAsPNG = useCallback(async (svgElement, filename) => {
    if (!svgElement) return;

    setIsExporting(true);
    try {
      const svgData = new XMLSerializer().serializeToString(svgElement);
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();

      const rect = svgElement.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;

      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
      });

      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);

      const link = document.createElement('a');
      link.download = filename || `network-${Date.now()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } finally {
      setIsExporting(false);
    }
  }, []);

  // 导出为JSON
  const exportAsJSON = useCallback((nodes, links, filename) => {
    const data = {
      nodes,
      links,
      exportTime: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `network-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, []);

  return useMemo(
    () => ({
      isExporting,
      exportAsPNG,
      exportAsJSON,
    }),
    [isExporting, exportAsPNG, exportAsJSON]
  );
};

/**
 * 使用完整的关联网络
 *
 * @param {Object} options - 配置选项
 * @returns {Object} 完整的关联网络状态
 */
export const useAssociationNetwork = (options = {}) => {
  const { knowledgeBaseId, width = 800, height = 600 } = options;

  // 数据查询
  const networkData = useNetworkData({ knowledgeBaseId });

  // 力导向布局
  const layout = useForceLayout(networkData.nodes, networkData.links, {
    width,
    height,
  });

  // 视图控制
  const view = useNetworkView();

  // 节点选择
  const selection = useNodeSelection();

  // 过滤器
  const filters = useNetworkFilters();

  // 统计
  const stats = useNetworkStats(networkData.nodes, networkData.links);

  // 导出
  const exportData = useNetworkExport();

  // 过滤后的数据
  const filteredNodes = useMemo(() => {
    return filters.filterNodes(networkData.nodes);
  }, [networkData.nodes, filters]);

  const filteredLinks = useMemo(() => {
    return filters.filterLinks(networkData.links);
  }, [networkData.links, filters]);

  return useMemo(
    () => ({
      // 数据
      nodes: networkData.nodes,
      links: networkData.links,
      filteredNodes,
      filteredLinks,
      positions: layout.positions,

      // 状态
      isLoading: networkData.isLoading,
      isCalculating: layout.isCalculating,

      // 视图
      zoom: view.zoom,
      pan: view.pan,
      isDragging: view.isDragging,

      // 选择
      selectedNode: selection.selectedNode,
      hoveredNode: selection.hoveredNode,

      // 过滤器
      nodeTypeFilter: filters.nodeTypeFilter,
      linkTypeFilter: filters.linkTypeFilter,
      minStrength: filters.minStrength,
      searchQuery: filters.searchQuery,
      hasActiveFilters: filters.hasActiveFilters,

      // 统计
      stats,

      // 操作
      zoomIn: view.zoomIn,
      zoomOut: view.zoomOut,
      resetView: view.resetView,
      selectNode: selection.selectNode,
      clearSelection: selection.clearSelection,
      hoverNode: selection.hoverNode,
      toggleNodeType: filters.toggleNodeType,
      toggleLinkType: filters.toggleLinkType,
      setMinStrength: filters.setMinStrength,
      setSearchQuery: filters.setSearchQuery,
      clearFilters: filters.clearFilters,
      recalculateLayout: layout.recalculate,
      exportAsPNG: exportData.exportAsPNG,
      exportAsJSON: exportData.exportAsJSON,

      // 拖拽
      startDrag: view.startDrag,
      drag: view.drag,
      endDrag: view.endDrag,
    }),
    [
      networkData,
      filteredNodes,
      filteredLinks,
      layout,
      view,
      selection,
      filters,
      stats,
      exportData,
    ]
  );
};

// ==================== 工具函数 ====================

/**
 * 计算两点间距离
 *
 * @param {Object} point1 - 点1
 * @param {Object} point2 - 点2
 * @returns {number} 距离
 */
export const calculateDistance = (point1, point2) => {
  const dx = point2.x - point1.x;
  const dy = point2.y - point1.y;
  return Math.sqrt(dx * dx + dy * dy);
};

/**
 * 计算节点度数
 *
 * @param {string} nodeId - 节点ID
 * @param {Array} links - 连线数组
 * @returns {number} 度数
 */
export const calculateNodeDegree = (nodeId, links) => {
  return links.filter((link) => link.source === nodeId || link.target === nodeId).length;
};

/**
 * 查找最短路径
 *
 * @param {string} startId - 起始节点ID
 * @param {string} endId - 目标节点ID
 * @param {Array} links - 连线数组
 * @returns {string[]|null} 路径节点ID数组
 */
export const findShortestPath = (startId, endId, links) => {
  if (startId === endId) return [startId];

  const graph = {};
  links.forEach((link) => {
    if (!graph[link.source]) graph[link.source] = [];
    if (!graph[link.target]) graph[link.target] = [];
    graph[link.source].push(link.target);
    graph[link.target].push(link.source);
  });

  const queue = [[startId]];
  const visited = new Set([startId]);

  while (queue.length > 0) {
    const path = queue.shift();
    const node = path[path.length - 1];

    if (node === endId) return path;

    const neighbors = graph[node] || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push([...path, neighbor]);
      }
    }
  }

  return null;
};

/**
 * 查找连通分量
 *
 * @param {Array} nodes - 节点数组
 * @param {Array} links - 连线数组
 * @returns {Array[]} 连通分量数组
 */
export const findConnectedComponents = (nodes, links) => {
  const visited = new Set();
  const components = [];

  const graph = {};
  links.forEach((link) => {
    if (!graph[link.source]) graph[link.source] = [];
    if (!graph[link.target]) graph[link.target] = [];
    graph[link.source].push(link.target);
    graph[link.target].push(link.source);
  });

  const dfs = (nodeId, component) => {
    visited.add(nodeId);
    component.push(nodeId);

    const neighbors = graph[nodeId] || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        dfs(neighbor, component);
      }
    }
  };

  nodes.forEach((node) => {
    if (!visited.has(node.id)) {
      const component = [];
      dfs(node.id, component);
      components.push(component);
    }
  });

  return components;
};
