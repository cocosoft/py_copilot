/**
 * 一体化知识查看器 Hooks - FE-009 一体化知识查看器
 *
 * 提供一体化知识查看器相关的数据获取和操作功能
 *
 * @task FE-009
 * @phase 前端功能拓展
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useMemo } from 'react';
import apiClient from '../services/apiClient';

/**
 * 使用知识单元列表
 *
 * @param {Object} options - 配置选项
 * @returns {Object} 知识单元数据和操作
 */
export const useKnowledgeUnits = (options = {}) => {
  const { knowledgeBaseId, filters = {}, enabled = true } = options;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['knowledge', 'units', knowledgeBaseId, filters],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/knowledge/units', {
        params: {
          knowledge_base_id: knowledgeBaseId,
          ...filters,
        },
      });
      return response.data;
    },
    enabled: !!knowledgeBaseId && enabled,
    staleTime: 2 * 60 * 1000, // 2分钟
  });

  return useMemo(
    () => ({
      units: data || [],
      isLoading,
      error,
      refetch,
    }),
    [data, isLoading, error, refetch]
  );
};

/**
 * 使用知识单元详情
 *
 * @param {string} unitId - 单元ID
 * @param {Object} options - 配置选项
 * @returns {Object} 知识单元详情
 */
export const useKnowledgeUnit = (unitId, options = {}) => {
  const { enabled = true } = options;

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'unit', unitId],
    queryFn: async () => {
      if (!unitId) return null;
      const response = await apiClient.get(`/api/v1/knowledge/units/${unitId}`);
      return response.data;
    },
    enabled: !!unitId && enabled,
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  return useMemo(
    () => ({
      unit: data,
      isLoading,
      error,
    }),
    [data, isLoading, error]
  );
};

/**
 * 使用知识单元关联
 *
 * @param {string} unitId - 单元ID
 * @param {Object} options - 配置选项
 * @returns {Object} 关联数据
 */
export const useUnitAssociations = (unitId, options = {}) => {
  const { enabled = true } = options;

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'associations', unitId],
    queryFn: async () => {
      if (!unitId) return [];
      const response = await apiClient.get(
        `/api/v1/knowledge/units/${unitId}/associations`
      );
      return response.data;
    },
    enabled: !!unitId && enabled,
    staleTime: 3 * 60 * 1000, // 3分钟
  });

  return useMemo(
    () => ({
      associations: data || [],
      isLoading,
      error,
    }),
    [data, isLoading, error]
  );
};

/**
 * 使用知识图谱数据
 *
 * @param {string} knowledgeBaseId - 知识库ID
 * @param {Object} options - 配置选项
 * @returns {Object} 图谱数据
 */
export const useKnowledgeGraph = (knowledgeBaseId, options = {}) => {
  const { depth = 2, enabled = true } = options;

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'graph', knowledgeBaseId, depth],
    queryFn: async () => {
      if (!knowledgeBaseId) return null;
      const response = await apiClient.get('/api/v1/knowledge/graph', {
        params: { knowledge_base_id: knowledgeBaseId, depth },
      });
      return response.data;
    },
    enabled: !!knowledgeBaseId && enabled,
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  return useMemo(
    () => ({
      graph: data,
      isLoading,
      error,
    }),
    [data, isLoading, error]
  );
};

/**
 * 使用实体列表
 *
 * @param {Object} options - 配置选项
 * @returns {Object} 实体数据
 */
export const useEntities = (options = {}) => {
  const { knowledgeBaseId, filters = {}, enabled = true } = options;

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'entities', knowledgeBaseId, filters],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/knowledge/entities', {
        params: {
          knowledge_base_id: knowledgeBaseId,
          ...filters,
        },
      });
      return response.data;
    },
    enabled: !!knowledgeBaseId && enabled,
    staleTime: 3 * 60 * 1000, // 3分钟
  });

  return useMemo(
    () => ({
      entities: data || [],
      isLoading,
      error,
    }),
    [data, isLoading, error]
  );
};

/**
 * 使用知识统计
 *
 * @param {string} knowledgeBaseId - 知识库ID
 * @param {Object} options - 配置选项
 * @returns {Object} 统计数据
 */
export const useKnowledgeStats = (knowledgeBaseId, options = {}) => {
  const { enabled = true } = options;

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'stats', knowledgeBaseId],
    queryFn: async () => {
      if (!knowledgeBaseId) return null;
      const response = await apiClient.get('/api/v1/knowledge/stats', {
        params: { knowledge_base_id: knowledgeBaseId },
      });
      return response.data;
    },
    enabled: !!knowledgeBaseId && enabled,
    staleTime: 5 * 60 * 1000, // 5分钟
    refetchInterval: 60 * 1000, // 每分钟刷新
  });

  return useMemo(
    () => ({
      stats: data,
      isLoading,
      error,
    }),
    [data, isLoading, error]
  );
};

/**
 * 使用知识搜索
 *
 * @returns {Object} 搜索功能和结果
 */
export const useKnowledgeSearch = () => {
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const search = useCallback(async (query, options = {}) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await apiClient.get('/api/v1/knowledge/search', {
        params: { q: query, ...options },
      });
      setSearchResults(response.data);
      return response.data;
    } catch (error) {
      console.error('搜索失败:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const clearSearch = useCallback(() => {
    setSearchResults([]);
  }, []);

  return useMemo(
    () => ({
      searchResults,
      isSearching,
      search,
      clearSearch,
    }),
    [searchResults, isSearching, search, clearSearch]
  );
};

/**
 * 使用知识单元选择
 *
 * @returns {Object} 选择状态和操作
 */
export const useUnitSelection = () => {
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [selectionHistory, setSelectionHistory] = useState([]);

  const selectUnit = useCallback((unit) => {
    setSelectedUnit(unit);
    if (unit) {
      setSelectionHistory((prev) => [
        { unit, timestamp: Date.now() },
        ...prev.slice(0, 19), // 保留最近20条
      ]);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedUnit(null);
  }, []);

  const goBack = useCallback(() => {
    if (selectionHistory.length > 1) {
      const previous = selectionHistory[1];
      setSelectedUnit(previous.unit);
      setSelectionHistory((prev) => prev.slice(1));
    }
  }, [selectionHistory]);

  return useMemo(
    () => ({
      selectedUnit,
      selectionHistory,
      selectUnit,
      clearSelection,
      goBack,
      canGoBack: selectionHistory.length > 1,
    }),
    [selectedUnit, selectionHistory, selectUnit, clearSelection, goBack]
  );
};

/**
 * 使用知识过滤器
 *
 * @param {Object} initialFilters - 初始过滤器
 * @returns {Object} 过滤器状态和操作
 */
export const useKnowledgeFilters = (initialFilters = {}) => {
  const [filters, setFilters] = useState({
    type: 'ALL',
    quality: { min: 0, max: 100 },
    dateRange: null,
    ...initialFilters,
  });

  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  const updateFilters = useCallback((updates) => {
    setFilters((prev) => ({
      ...prev,
      ...updates,
    }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      type: 'ALL',
      quality: { min: 0, max: 100 },
      dateRange: null,
    });
  }, []);

  const clearFilter = useCallback((key) => {
    setFilters((prev) => {
      const newFilters = { ...prev };
      delete newFilters[key];
      return newFilters;
    });
  }, []);

  const hasActiveFilters = useMemo(() => {
    return (
      filters.type !== 'ALL' ||
      filters.quality.min > 0 ||
      filters.quality.max < 100 ||
      filters.dateRange !== null
    );
  }, [filters]);

  return useMemo(
    () => ({
      filters,
      updateFilter,
      updateFilters,
      resetFilters,
      clearFilter,
      hasActiveFilters,
    }),
    [filters, updateFilter, updateFilters, resetFilters, clearFilter, hasActiveFilters]
  );
};

/**
 * 使用知识导出
 *
 * @returns {Object} 导出功能
 */
export const useKnowledgeExport = () => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);

  const exportAsJSON = useCallback(async (data, filename) => {
    setIsExporting(true);
    setExportProgress(0);

    try {
      // 模拟导出进度
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        setExportProgress(i);
      }

      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `knowledge-export-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
      setExportProgress(0);
    }
  }, []);

  const exportAsCSV = useCallback(async (data, filename) => {
    setIsExporting(true);
    setExportProgress(0);

    try {
      if (!data || data.length === 0) return;

      // 模拟导出进度
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        setExportProgress(i);
      }

      const headers = Object.keys(data[0]);
      const rows = data.map((row) =>
        headers.map((h) => JSON.stringify(row[h])).join(',')
      );
      const csv = [headers.join(','), ...rows].join('\n');

      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `knowledge-export-${Date.now()}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
      setExportProgress(0);
    }
  }, []);

  return useMemo(
    () => ({
      isExporting,
      exportProgress,
      exportAsJSON,
      exportAsCSV,
    }),
    [isExporting, exportProgress, exportAsJSON, exportAsCSV]
  );
};

/**
 * 使用完整的一体化知识查看器
 *
 * @param {string} knowledgeBaseId - 知识库ID
 * @returns {Object} 完整的一体化知识查看器状态
 */
export const useUnifiedKnowledgeViewer = (knowledgeBaseId) => {
  const queryClient = useQueryClient();

  // 数据查询
  const unitsQuery = useKnowledgeUnits({ knowledgeBaseId });
  const statsQuery = useKnowledgeStats(knowledgeBaseId);
  const graphQuery = useKnowledgeGraph(knowledgeBaseId);

  // 选择管理
  const selection = useUnitSelection();

  // 过滤器
  const filters = useKnowledgeFilters();

  // 搜索
  const search = useKnowledgeSearch();

  // 导出
  const exportData = useKnowledgeExport();

  // 刷新所有数据
  const refreshAll = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['knowledge'] });
  }, [queryClient]);

  // 过滤后的单元
  const filteredUnits = useMemo(() => {
    let result = unitsQuery.units;

    // 类型过滤
    if (filters.filters.type !== 'ALL') {
      result = result.filter((unit) => unit.type === filters.filters.type);
    }

    // 质量过滤
    result = result.filter(
      (unit) =>
        unit.metadata.quality >= filters.filters.quality.min &&
        unit.metadata.quality <= filters.filters.quality.max
    );

    return result;
  }, [unitsQuery.units, filters.filters]);

  // 实体列表
  const entities = useMemo(() => {
    return filteredUnits.filter((unit) => unit.type === 'ENTITY');
  }, [filteredUnits]);

  return useMemo(
    () => ({
      // 数据
      units: unitsQuery.units,
      filteredUnits,
      entities,
      associations: graphQuery.graph?.associations || [],
      stats: statsQuery.stats,
      graph: graphQuery.graph,

      // 状态
      isLoading:
        unitsQuery.isLoading || statsQuery.isLoading || graphQuery.isLoading,

      // 选择
      selectedUnit: selection.selectedUnit,
      selectionHistory: selection.selectionHistory,
      selectUnit: selection.selectUnit,
      clearSelection: selection.clearSelection,

      // 过滤器
      filters: filters.filters,
      updateFilter: filters.updateFilter,
      resetFilters: filters.resetFilters,
      hasActiveFilters: filters.hasActiveFilters,

      // 搜索
      searchResults: search.searchResults,
      isSearching: search.isSearching,
      search: search.search,
      clearSearch: search.clearSearch,

      // 导出
      isExporting: exportData.isExporting,
      exportProgress: exportData.exportProgress,
      exportAsJSON: exportData.exportAsJSON,
      exportAsCSV: exportData.exportAsCSV,

      // 操作
      refreshAll,
    }),
    [
      unitsQuery,
      filteredUnits,
      entities,
      graphQuery,
      statsQuery,
      selection,
      filters,
      search,
      exportData,
      refreshAll,
    ]
  );
};

// ==================== 工具函数 ====================

/**
 * 获取知识单元类型图标
 *
 * @param {string} type - 单元类型
 * @returns {string} 图标名称
 */
export const getUnitTypeIcon = (type) => {
  const icons = {
    DOCUMENT: 'FileText',
    CHUNK: 'Layers',
    ENTITY: 'Tag',
    RELATIONSHIP: 'Link',
    CONCEPT: 'Box',
    FACT: 'CheckCircle',
  };
  return icons[type] || 'Layers';
};

/**
 * 获取知识单元类型颜色
 *
 * @param {string} type - 单元类型
 * @returns {string} 颜色代码
 */
export const getUnitTypeColor = (type) => {
  const colors = {
    DOCUMENT: '#1890ff',
    CHUNK: '#52c41a',
    ENTITY: '#faad14',
    RELATIONSHIP: '#722ed1',
    CONCEPT: '#eb2f96',
    FACT: '#13c2c2',
  };
  return colors[type] || '#8c8c8c';
};

/**
 * 获取关联类型标签
 *
 * @param {string} type - 关联类型
 * @returns {string} 标签文本
 */
export const getAssociationTypeLabel = (type) => {
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
 * 计算知识单元统计
 *
 * @param {Array} units - 知识单元数组
 * @returns {Object} 统计数据
 */
export const calculateUnitStats = (units) => {
  if (!units || units.length === 0) {
    return {
      total: 0,
      typeCount: {},
      avgQuality: 0,
      totalVectors: 0,
      totalEntities: 0,
    };
  }

  const typeCount = {};
  let totalQuality = 0;
  let totalVectors = 0;
  let totalEntities = 0;

  units.forEach((unit) => {
    typeCount[unit.type] = (typeCount[unit.type] || 0) + 1;
    totalQuality += unit.metadata?.quality || 0;
    totalVectors += unit.metadata?.vectorCount || 0;
    totalEntities += unit.metadata?.entityCount || 0;
  });

  return {
    total: units.length,
    typeCount,
    avgQuality: (totalQuality / units.length).toFixed(1),
    totalVectors,
    totalEntities,
  };
};

/**
 * 构建关联网络
 *
 * @param {Array} units - 知识单元数组
 * @param {Array} associations - 关联数组
 * @returns {Object} 网络数据
 */
export const buildAssociationNetwork = (units, associations) => {
  const unitMap = new Map(units.map((u) => [u.id, u]));

  const nodes = units.map((unit) => ({
    id: unit.id,
    label: unit.title,
    type: unit.type,
    color: getUnitTypeColor(unit.type),
  }));

  const links = associations
    .filter((assoc) => unitMap.has(assoc.sourceId) && unitMap.has(assoc.targetId))
    .map((assoc) => ({
      source: assoc.sourceId,
      target: assoc.targetId,
      type: assoc.type,
      strength: assoc.strength,
    }));

  return { nodes, links };
};
