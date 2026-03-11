/**
 * 质量评估 Hooks - FE-004 质量评估面板
 *
 * 提供质量评估相关的数据获取和操作功能
 *
 * @task FE-004
 * @phase 前端功能拓展
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useMemo, useCallback } from 'react';
import apiClient from '../services/apiClient';
import { queryKeys } from '../config/queryClient';

/**
 * 使用文档质量评估数据
 *
 * @param {string} documentId - 文档ID
 * @param {Object} options - 配置选项
 * @returns {Object} 查询结果
 */
export const useDocumentQuality = (documentId, options = {}) => {
  return useQuery({
    queryKey: queryKeys.knowledgeDocument(documentId),
    queryFn: async () => {
      if (!documentId) return null;
      const response = await apiClient.get(
        `/api/v1/knowledge/documents/${documentId}/quality`
      );
      return response.data;
    },
    enabled: !!documentId,
    staleTime: 2 * 60 * 1000, // 2分钟
    ...options,
  });
};

/**
 * 使用知识库质量统计
 *
 * @param {string} knowledgeBaseId - 知识库ID
 * @param {Object} options - 配置选项
 * @returns {Object} 查询结果
 */
export const useKnowledgeBaseQualityStats = (knowledgeBaseId, options = {}) => {
  return useQuery({
    queryKey: [...queryKeys.knowledge, 'quality-stats', knowledgeBaseId],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/knowledge/quality/stats', {
        params: { knowledgeBaseId },
      });
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5分钟
    ...options,
  });
};

/**
 * 使用异常片段列表
 *
 * @param {Object} params - 查询参数
 * @param {Object} options - 配置选项
 * @returns {Object} 查询结果
 */
export const useAnomalyChunks = (params = {}, options = {}) => {
  const { documentId, knowledgeBaseId, anomalyType, minScore, page = 1, pageSize = 20 } = params;

  return useQuery({
    queryKey: [...queryKeys.knowledge, 'anomaly-chunks', params],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/knowledge/quality/anomalies', {
        params: {
          documentId,
          knowledgeBaseId,
          anomalyType,
          minScore,
          page,
          pageSize,
        },
      });
      return response.data;
    },
    staleTime: 1 * 60 * 1000, // 1分钟
    ...options,
  });
};

/**
 * 使用质量趋势数据
 *
 * @param {Object} params - 查询参数
 * @param {Object} options - 配置选项
 * @returns {Object} 查询结果
 */
export const useQualityTrend = (params = {}, options = {}) => {
  const { knowledgeBaseId, documentId, days = 30 } = params;

  return useQuery({
    queryKey: [...queryKeys.knowledge, 'quality-trend', params],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/knowledge/quality/trend', {
        params: {
          knowledgeBaseId,
          documentId,
          days,
        },
      });
      return response.data;
    },
    staleTime: 10 * 60 * 1000, // 10分钟
    ...options,
  });
};

/**
 * 使用质量维度评分
 *
 * @param {string} documentId - 文档ID
 * @param {Object} options - 配置选项
 * @returns {Object} 查询结果
 */
export const useQualityDimensions = (documentId, options = {}) => {
  return useQuery({
    queryKey: [...queryKeys.knowledge, 'quality-dimensions', documentId],
    queryFn: async () => {
      if (!documentId) return null;
      const response = await apiClient.get(
        `/api/v1/knowledge/documents/${documentId}/quality/dimensions`
      );
      return response.data;
    },
    enabled: !!documentId,
    staleTime: 5 * 60 * 1000, // 5分钟
    ...options,
  });
};

/**
 * 使用片段质量详情
 *
 * @param {string} chunkId - 片段ID
 * @param {Object} options - 配置选项
 * @returns {Object} 查询结果
 */
export const useChunkQuality = (chunkId, options = {}) => {
  return useQuery({
    queryKey: [...queryKeys.knowledge, 'chunk-quality', chunkId],
    queryFn: async () => {
      if (!chunkId) return null;
      const response = await apiClient.get(
        `/api/v1/knowledge/chunks/${chunkId}/quality`
      );
      return response.data;
    },
    enabled: !!chunkId,
    staleTime: 2 * 60 * 1000, // 2分钟
    ...options,
  });
};

// ==================== Mutations ====================

/**
 * 使用重处理片段 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useReprocessChunk = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (chunkId) => {
      const response = await apiClient.post(
        `/api/v1/knowledge/chunks/${chunkId}/reprocess`
      );
      return response.data;
    },
    onSuccess: (_, chunkId) => {
      // 清除相关缓存
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.knowledge, 'chunk-quality', chunkId],
      });
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.knowledge, 'anomaly-chunks'],
      });
    },
  });
};

/**
 * 使用批量重处理 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useBatchReprocessChunks = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (chunkIds) => {
      const response = await apiClient.post('/api/v1/knowledge/chunks/batch-reprocess', {
        chunkIds,
      });
      return response.data;
    },
    onSuccess: () => {
      // 清除所有质量相关缓存
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.knowledge, 'chunk-quality'],
      });
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.knowledge, 'anomaly-chunks'],
      });
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.knowledge, 'quality-stats'],
      });
    },
  });
};

/**
 * 使用重处理文档 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useReprocessDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId) => {
      const response = await apiClient.post(
        `/api/v1/knowledge/documents/${documentId}/reprocess`
      );
      return response.data;
    },
    onSuccess: (_, documentId) => {
      // 清除文档相关缓存
      queryClient.invalidateQueries({
        queryKey: queryKeys.knowledgeDocument(documentId),
      });
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.knowledge, 'quality-stats'],
      });
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.knowledge, 'anomaly-chunks'],
      });
    },
  });
};

// ==================== 组合 Hooks ====================

/**
 * 使用完整的质量评估数据
 *
 * @param {string} documentId - 文档ID
 * @returns {Object} 完整质量数据
 */
export const useCompleteQualityData = (documentId) => {
  const qualityQuery = useDocumentQuality(documentId);
  const dimensionsQuery = useQualityDimensions(documentId);
  const trendQuery = useQualityTrend({ documentId });

  const isLoading = qualityQuery.isLoading || dimensionsQuery.isLoading || trendQuery.isLoading;
  const error = qualityQuery.error || dimensionsQuery.error || trendQuery.error;

  const data = useMemo(() => {
    if (!qualityQuery.data) return null;

    return {
      quality: qualityQuery.data,
      dimensions: dimensionsQuery.data,
      trend: trendQuery.data,
    };
  }, [qualityQuery.data, dimensionsQuery.data, trendQuery.data]);

  const refetch = useCallback(() => {
    qualityQuery.refetch();
    dimensionsQuery.refetch();
    trendQuery.refetch();
  }, [qualityQuery, dimensionsQuery, trendQuery]);

  return {
    data,
    isLoading,
    error,
    refetch,
  };
};

/**
 * 使用质量评估操作
 *
 * @returns {Object} 质量评估操作函数
 */
export const useQualityActions = () => {
  const reprocessChunk = useReprocessChunk();
  const batchReprocess = useBatchReprocessChunks();
  const reprocessDocument = useReprocessDocument();

  return useMemo(
    () => ({
      reprocessChunk: reprocessChunk.mutateAsync,
      reprocessChunkLoading: reprocessChunk.isPending,
      batchReprocess: batchReprocess.mutateAsync,
      batchReprocessLoading: batchReprocess.isPending,
      reprocessDocument: reprocessDocument.mutateAsync,
      reprocessDocumentLoading: reprocessDocument.isPending,
    }),
    [reprocessChunk, batchReprocess, reprocessDocument]
  );
};

/**
 * 使用质量评估状态
 *
 * @param {string} documentId - 文档ID
 * @returns {Object} 质量评估状态和操作
 */
export const useQualityAssessment = (documentId) => {
  const data = useCompleteQualityData(documentId);
  const actions = useQualityActions();
  const anomalyQuery = useAnomalyChunks({ documentId });

  return useMemo(
    () => ({
      // 数据
      qualityData: data.data?.quality,
      dimensionData: data.data?.dimensions,
      trendData: data.data?.trend,
      anomalyChunks: anomalyQuery.data?.items || [],

      // 状态
      isLoading: data.isLoading || anomalyQuery.isLoading,
      error: data.error || anomalyQuery.error,

      // 操作
      refetch: () => {
        data.refetch();
        anomalyQuery.refetch();
      },
      ...actions,
    }),
    [data, anomalyQuery, actions]
  );
};

// ==================== 工具函数 ====================

/**
 * 获取质量等级
 *
 * @param {number} score - 质量分数
 * @returns {string} 质量等级
 */
export const getQualityLevel = (score) => {
  if (score >= 90) return 'excellent';
  if (score >= 70) return 'good';
  if (score >= 50) return 'fair';
  return 'poor';
};

/**
 * 获取质量等级配置
 *
 * @param {string} level - 质量等级
 * @returns {Object} 等级配置
 */
export const getQualityLevelConfig = (level) => {
  const configs = {
    excellent: { color: '#52c41a', label: '优秀', icon: '✓' },
    good: { color: '#1890ff', label: '良好', icon: '✓' },
    fair: { color: '#faad14', label: '一般', icon: '!' },
    poor: { color: '#ff4d4f', label: '较差', icon: '✕' },
  };
  return configs[level] || configs.poor;
};

/**
 * 格式化质量分数
 *
 * @param {number} score - 质量分数
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的分数
 */
export const formatQualityScore = (score, decimals = 1) => {
  if (score === null || score === undefined) return '-';
  return score.toFixed(decimals);
};

/**
 * 计算质量趋势
 *
 * @param {Array} trendData - 趋势数据
 * @returns {Object} 趋势信息
 */
export const calculateQualityTrend = (trendData) => {
  if (!trendData || trendData.length < 2) {
    return { trend: 'stable', value: 0 };
  }

  const first = trendData[0].score;
  const last = trendData[trendData.length - 1].score;
  const change = last - first;
  const percentChange = (change / first) * 100;

  return {
    trend: change > 0 ? 'up' : change < 0 ? 'down' : 'stable',
    value: percentChange.toFixed(1),
    absoluteChange: change.toFixed(1),
  };
};
