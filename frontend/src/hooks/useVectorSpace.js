/**
 * 向量空间 Hooks - FE-006 向量空间3D可视化
 *
 * 提供向量空间相关的数据获取和操作功能
 *
 * @task FE-006
 * @phase 前端功能拓展
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useMemo, useRef } from 'react';
import apiClient from '../services/apiClient';
import { queryKeys } from '../config/queryClient';

/**
 * 使用向量空间数据查询
 *
 * @param {string} knowledgeBaseId - 知识库ID
 * @param {Object} options - 查询选项
 * @returns {Object} 查询结果
 */
export const useVectorSpaceData = (knowledgeBaseId, options = {}) => {
  const { sampleSize = 1000, enabled = true } = options;

  return useQuery({
    queryKey: queryKeys.knowledge.vectorSpace(knowledgeBaseId),
    queryFn: async () => {
      if (!knowledgeBaseId) return null;

      const response = await apiClient.get(
        `/api/v1/knowledge/${knowledgeBaseId}/vector-space`,
        {
          params: { sampleSize },
        }
      );
      return response.data;
    },
    enabled: !!knowledgeBaseId && enabled,
    staleTime: 5 * 60 * 1000, // 5分钟
    cacheTime: 10 * 60 * 1000, // 10分钟
  });
};

/**
 * 使用向量聚类数据
 *
 * @param {string} knowledgeBaseId - 知识库ID
 * @param {Object} options - 查询选项
 * @returns {Object} 查询结果
 */
export const useVectorClusters = (knowledgeBaseId, options = {}) => {
  const { clusterCount = 5, enabled = true } = options;

  return useQuery({
    queryKey: [...queryKeys.knowledge.vectorSpace(knowledgeBaseId), 'clusters', clusterCount],
    queryFn: async () => {
      if (!knowledgeBaseId) return null;

      const response = await apiClient.get(
        `/api/v1/knowledge/${knowledgeBaseId}/clusters`,
        {
          params: { clusterCount },
        }
      );
      return response.data;
    },
    enabled: !!knowledgeBaseId && enabled,
    staleTime: 10 * 60 * 1000, // 10分钟
  });
};

/**
 * 使用向量搜索
 *
 * @returns {Object} 搜索Mutation
 */
export const useVectorSearch = () => {
  return useMutation({
    mutationFn: async ({ knowledgeBaseId, query, topK = 10 }) => {
      const response = await apiClient.post(
        `/api/v1/knowledge/${knowledgeBaseId}/vector-search`,
        {
          query,
          topK,
        }
      );
      return response.data;
    },
  });
};

/**
 * 使用3D相机控制
 *
 * @param {Object} initialCamera - 初始相机参数
 * @returns {Object} 相机状态和控制函数
 */
export const useCamera3D = (initialCamera = {}) => {
  const [camera, setCamera] = useState({
    x: 0,
    y: 0,
    z: 500,
    rotX: 0.3,
    rotY: 0.5,
    zoom: 1,
    ...initialCamera,
  });

  const [isAutoRotating, setIsAutoRotating] = useState(false);
  const animationRef = useRef(null);

  /**
   * 重置相机
   */
  const resetCamera = useCallback(() => {
    setCamera({
      x: 0,
      y: 0,
      z: 500,
      rotX: 0.3,
      rotY: 0.5,
      zoom: 1,
    });
  }, []);

  /**
   * 缩放
   */
  const zoom = useCallback((factor) => {
    setCamera((prev) => ({
      ...prev,
      zoom: Math.max(0.1, Math.min(5, prev.zoom * factor)),
    }));
  }, []);

  /**
   * 旋转
   */
  const rotate = useCallback((deltaX, deltaY) => {
    setCamera((prev) => ({
      ...prev,
      rotY: prev.rotY + deltaX * 0.01,
      rotX: Math.max(-Math.PI / 2, Math.min(Math.PI / 2, prev.rotX - deltaY * 0.01)),
    }));
  }, []);

  /**
   * 平移
   */
  const pan = useCallback((deltaX, deltaY) => {
    setCamera((prev) => ({
      ...prev,
      x: prev.x + deltaX,
      y: prev.y - deltaY,
    }));
  }, []);

  /**
   * 开始自动旋转
   */
  const startAutoRotate = useCallback(() => {
    setIsAutoRotating(true);

    const animate = () => {
      setCamera((prev) => ({
        ...prev,
        rotY: prev.rotY + 0.005,
      }));
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);
  }, []);

  /**
   * 停止自动旋转
   */
  const stopAutoRotate = useCallback(() => {
    setIsAutoRotating(false);
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
  }, []);

  /**
   * 切换自动旋转
   */
  const toggleAutoRotate = useCallback(() => {
    if (isAutoRotating) {
      stopAutoRotate();
    } else {
      startAutoRotate();
    }
  }, [isAutoRotating, startAutoRotate, stopAutoRotate]);

  return useMemo(
    () => ({
      camera,
      isAutoRotating,
      setCamera,
      resetCamera,
      zoom,
      rotate,
      pan,
      startAutoRotate,
      stopAutoRotate,
      toggleAutoRotate,
    }),
    [camera, isAutoRotating, resetCamera, zoom, rotate, pan, startAutoRotate, stopAutoRotate, toggleAutoRotate]
  );
};

/**
 * 使用点选择
 *
 * @param {Array} points - 点数组
 * @returns {Object} 选择状态和操作
 */
export const usePointSelection = (points = []) => {
  const [selectedIds, setSelectedIds] = useState([]);
  const [hoveredId, setHoveredId] = useState(null);

  /**
   * 选择点
   */
  const selectPoint = useCallback((pointId) => {
    setSelectedIds((prev) => {
      if (prev.includes(pointId)) {
        return prev.filter((id) => id !== pointId);
      }
      return [...prev, pointId];
    });
  }, []);

  /**
   * 设置悬停点
   */
  const hoverPoint = useCallback((pointId) => {
    setHoveredId(pointId);
  }, []);

  /**
   * 清空选择
   */
  const clearSelection = useCallback(() => {
    setSelectedIds([]);
  }, []);

  /**
   * 全选
   */
  const selectAll = useCallback(() => {
    setSelectedIds(points.map((p) => p.id));
  }, [points]);

  /**
   * 获取选中的点
   */
  const selectedPoints = useMemo(() => {
    return points.filter((p) => selectedIds.includes(p.id));
  }, [points, selectedIds]);

  /**
   * 获取悬停的点
   */
  const hoveredPoint = useMemo(() => {
    return points.find((p) => p.id === hoveredId);
  }, [points, hoveredId]);

  return useMemo(
    () => ({
      selectedIds,
      hoveredId,
      selectedPoints,
      hoveredPoint,
      selectPoint,
      hoverPoint,
      clearSelection,
      selectAll,
    }),
    [selectedIds, hoveredId, selectedPoints, hoveredPoint, selectPoint, hoverPoint, clearSelection, selectAll]
  );
};

/**
 * 使用聚类过滤
 *
 * @param {Array} points - 点数组
 * @returns {Object} 过滤状态和操作
 */
export const useClusterFilter = (points = []) => {
  const [visibleClusters, setVisibleClusters] = useState({});

  // 获取所有聚类
  const clusters = useMemo(() => {
    const clusterSet = new Map();
    points.forEach((point) => {
      if (!clusterSet.has(point.cluster)) {
        clusterSet.set(point.cluster, {
          id: point.cluster,
          color: point.color,
          count: 0,
        });
      }
      clusterSet.get(point.cluster).count++;
    });
    return Array.from(clusterSet.values()).sort((a, b) => a.id - b.id);
  }, [points]);

  /**
   * 切换聚类可见性
   */
  const toggleCluster = useCallback((clusterId) => {
    setVisibleClusters((prev) => ({
      ...prev,
      [clusterId]: prev[clusterId] === false ? true : false,
    }));
  }, []);

  /**
   * 显示所有聚类
   */
  const showAllClusters = useCallback(() => {
    setVisibleClusters({});
  }, []);

  /**
   * 隐藏所有聚类
   */
  const hideAllClusters = useCallback(() => {
    const allHidden = {};
    clusters.forEach((c) => {
      allHidden[c.id] = false;
    });
    setVisibleClusters(allHidden);
  }, [clusters]);

  /**
   * 只显示指定聚类
   */
  const showOnlyCluster = useCallback((clusterId) => {
    const onlyOne = {};
    clusters.forEach((c) => {
      onlyOne[c.id] = c.id === clusterId;
    });
    setVisibleClusters(onlyOne);
  }, [clusters]);

  /**
   * 过滤后的点
   */
  const filteredPoints = useMemo(() => {
    return points.filter((point) => {
      return visibleClusters[point.cluster] !== false;
    });
  }, [points, visibleClusters]);

  return useMemo(
    () => ({
      clusters,
      visibleClusters,
      filteredPoints,
      toggleCluster,
      showAllClusters,
      hideAllClusters,
      showOnlyCluster,
    }),
    [clusters, visibleClusters, filteredPoints, toggleCluster, showAllClusters, hideAllClusters, showOnlyCluster]
  );
};

/**
 * 使用3D投影计算
 *
 * @returns {Object} 投影函数
 */
export const use3DProjection = () => {
  /**
   * 3D到2D投影
   */
  const project = useCallback((point, camera, width, height) => {
    // 应用相机旋转
    const cosX = Math.cos(camera.rotX);
    const sinX = Math.sin(camera.rotX);
    const cosY = Math.cos(camera.rotY);
    const sinY = Math.sin(camera.rotY);

    // 旋转点
    const x1 = point.x * cosY - point.z * sinY;
    const z1 = point.x * sinY + point.z * cosY;
    const y1 = point.y * cosX - z1 * sinX;
    const z2 = point.y * sinX + z1 * cosX;

    // 应用相机位置
    const x2 = x1 - camera.x;
    const y2 = y1 - camera.y;
    const z3 = z2 - camera.z;

    // 透视投影
    const fov = 800;
    const scale = (fov / (fov + z3)) * camera.zoom;

    return {
      x: width / 2 + x2 * scale,
      y: height / 2 - y2 * scale,
      scale,
      depth: z3,
    };
  }, []);

  /**
   * 批量投影
   */
  const projectBatch = useCallback((points, camera, width, height) => {
    return points.map((point) => ({
      ...point,
      projected: project(point, camera, width, height),
    }));
  }, [project]);

  return useMemo(
    () => ({
      project,
      projectBatch,
    }),
    [project, projectBatch]
  );
};

/**
 * 使用完整的向量空间
 *
 * @param {string} knowledgeBaseId - 知识库ID
 * @returns {Object} 完整的向量空间状态
 */
export const useVectorSpace = (knowledgeBaseId) => {
  const { data: vectorData, isLoading, error } = useVectorSpaceData(knowledgeBaseId);
  const { data: clusterData } = useVectorClusters(knowledgeBaseId);
  const camera = useCamera3D();
  const selection = usePointSelection(vectorData?.points || []);
  const clusterFilter = useClusterFilter(vectorData?.points || []);
  const projection = use3DProjection();
  const searchMutation = useVectorSearch();

  // 合并聚类信息到点数据
  const enrichedPoints = useMemo(() => {
    if (!vectorData?.points) return [];

    return vectorData.points.map((point) => ({
      ...point,
      clusterInfo: clusterData?.clusters?.find((c) => c.id === point.cluster),
    }));
  }, [vectorData, clusterData]);

  // 搜索向量
  const searchVectors = useCallback(
    async (query, topK = 10) => {
      if (!knowledgeBaseId) return;

      const results = await searchMutation.mutateAsync({
        knowledgeBaseId,
        query,
        topK,
      });

      // 高亮搜索结果
      const resultIds = results.map((r) => r.id);
      selection.selectPoint(resultIds);

      return results;
    },
    [knowledgeBaseId, searchMutation, selection]
  );

  return useMemo(
    () => ({
      // 数据
      points: enrichedPoints,
      clusters: clusterData?.clusters || [],
      isLoading,
      error,

      // 相机控制
      camera,

      // 点选择
      selection,

      // 聚类过滤
      clusterFilter,

      // 投影
      projection,

      // 搜索
      searchVectors,
      isSearching: searchMutation.isPending,
    }),
    [
      enrichedPoints,
      clusterData,
      isLoading,
      error,
      camera,
      selection,
      clusterFilter,
      projection,
      searchVectors,
      searchMutation.isPending,
    ]
  );
};

// ==================== 工具函数 ====================

/**
 * 生成聚类颜色
 *
 * @param {number} clusterId - 聚类ID
 * @returns {string} 颜色值
 */
export const getClusterColor = (clusterId) => {
  const colors = [
    '#1890ff', '#52c41a', '#faad14', '#f5222d',
    '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16',
  ];
  return colors[clusterId % colors.length];
};

/**
 * 计算点之间的距离
 *
 * @param {Point3D} p1 - 点1
 * @param {Point3D} p2 - 点2
 * @returns {number} 欧几里得距离
 */
export const calculateDistance = (p1, p2) => {
  return Math.sqrt(
    Math.pow(p2.x - p1.x, 2) +
    Math.pow(p2.y - p1.y, 2) +
    Math.pow(p2.z - p1.z, 2)
  );
};

/**
 * 计算聚类中心
 *
 * @param {Array} points - 点数组
 * @returns {Object} 中心点坐标
 */
export const calculateClusterCenter = (points) => {
  if (points.length === 0) return { x: 0, y: 0, z: 0 };

  const sum = points.reduce(
    (acc, p) => ({
      x: acc.x + p.x,
      y: acc.y + p.y,
      z: acc.z + p.z,
    }),
    { x: 0, y: 0, z: 0 }
  );

  return {
    x: sum.x / points.length,
    y: sum.y / points.length,
    z: sum.z / points.length,
  };
};

/**
 * 归一化坐标
 *
 * @param {Array} points - 点数组
 * @returns {Array} 归一化后的点数组
 */
export const normalizeCoordinates = (points) => {
  if (points.length === 0) return [];

  // 找到边界
  const bounds = points.reduce(
    (acc, p) => ({
      minX: Math.min(acc.minX, p.x),
      maxX: Math.max(acc.maxX, p.x),
      minY: Math.min(acc.minY, p.y),
      maxY: Math.max(acc.maxY, p.y),
      minZ: Math.min(acc.minZ, p.z),
      maxZ: Math.max(acc.maxZ, p.z),
    }),
    {
      minX: Infinity,
      maxX: -Infinity,
      minY: Infinity,
      maxY: -Infinity,
      minZ: Infinity,
      maxZ: -Infinity,
    }
  );

  const rangeX = bounds.maxX - bounds.minX || 1;
  const rangeY = bounds.maxY - bounds.minY || 1;
  const rangeZ = bounds.maxZ - bounds.minZ || 1;

  // 归一化到 [-1, 1]
  return points.map((p) => ({
    ...p,
    x: ((p.x - bounds.minX) / rangeX - 0.5) * 2,
    y: ((p.y - bounds.minY) / rangeY - 0.5) * 2,
    z: ((p.z - bounds.minZ) / rangeZ - 0.5) * 2,
  }));
};
