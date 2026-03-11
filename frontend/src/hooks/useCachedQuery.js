/**
 * 带缓存的请求 Hooks - FE-003 请求缓存优化
 *
 * 基于 React Query 和自定义缓存的请求管理
 *
 * @task FE-003
 * @phase 前端界面优化
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import requestCacheService from '../services/requestCacheService';
import apiClient from '../services/apiClient';

/**
 * 知识库相关的 Query Keys
 */
export const knowledgeQueryKeys = {
  all: ['knowledge'],
  bases: () => [...knowledgeQueryKeys.all, 'bases'],
  base: (id) => [...knowledgeQueryKeys.all, 'base', id],
  documents: (params) => [...knowledgeQueryKeys.all, 'documents', params],
  document: (id) => [...knowledgeQueryKeys.all, 'document', id],
  chunks: (documentId, params) => [...knowledgeQueryKeys.all, 'chunks', documentId, params],
  chunk: (id) => [...knowledgeQueryKeys.all, 'chunk', id],
  entities: (params) => [...knowledgeQueryKeys.all, 'entities', params],
  entity: (id) => [...knowledgeQueryKeys.all, 'entity', id],
  relationships: (params) => [...knowledgeQueryKeys.all, 'relationships', params],
  search: (query) => [...knowledgeQueryKeys.all, 'search', query],
  stats: (baseId) => [...knowledgeQueryKeys.all, 'stats', baseId],
  processing: (documentId) => [...knowledgeQueryKeys.all, 'processing', documentId],
};

/**
 * 使用带缓存的知识库列表查询
 */
export const useKnowledgeBases = (options = {}) => {
  const { skipCache = false, ...queryOptions } = options;

  return useQuery({
    queryKey: knowledgeQueryKeys.bases(),
    queryFn: async () => {
      return requestCacheService.request(
        'knowledge.bases',
        {},
        async () => {
          const response = await apiClient.get('/api/v1/knowledge/bases');
          return response.data;
        },
        { skipCache }
      );
    },
    staleTime: 10 * 60 * 1000, // 10分钟
    cacheTime: 15 * 60 * 1000, // 15分钟
    ...queryOptions,
  });
};

/**
 * 使用带缓存的文档列表查询
 */
export const useDocuments = (params = {}, options = {}) => {
  const { skipCache = false, ...queryOptions } = options;

  return useQuery({
    queryKey: knowledgeQueryKeys.documents(params),
    queryFn: async () => {
      return requestCacheService.request(
        'knowledge.documents',
        params,
        async () => {
          const response = await apiClient.get('/api/v1/knowledge/documents', {
            params,
          });
          return response.data;
        },
        { skipCache }
      );
    },
    staleTime: 2 * 60 * 1000, // 2分钟
    cacheTime: 5 * 60 * 1000, // 5分钟
    ...queryOptions,
  });
};

/**
 * 使用带缓存的文档详情查询
 */
export const useDocument = (id, options = {}) => {
  const { skipCache = false, ...queryOptions } = options;

  return useQuery({
    queryKey: knowledgeQueryKeys.document(id),
    queryFn: async () => {
      if (!id) return null;

      return requestCacheService.request(
        'knowledge.document',
        { id },
        async () => {
          const response = await apiClient.get(`/api/v1/knowledge/documents/${id}`);
          return response.data;
        },
        { skipCache }
      );
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5分钟
    cacheTime: 10 * 60 * 1000, // 10分钟
    ...queryOptions,
  });
};

/**
 * 使用带缓存的片段列表查询
 */
export const useChunks = (documentId, params = {}, options = {}) => {
  const { skipCache = false, ...queryOptions } = options;

  return useQuery({
    queryKey: knowledgeQueryKeys.chunks(documentId, params),
    queryFn: async () => {
      if (!documentId) return { items: [], total: 0 };

      return requestCacheService.request(
        'knowledge.chunks',
        { documentId, ...params },
        async () => {
          const response = await apiClient.get(
            `/api/v1/knowledge/documents/${documentId}/chunks`,
            { params }
          );
          return response.data;
        },
        { skipCache }
      );
    },
    enabled: !!documentId,
    staleTime: 1 * 60 * 1000, // 1分钟
    cacheTime: 3 * 60 * 1000, // 3分钟
    ...queryOptions,
  });
};

/**
 * 使用带缓存的实体列表查询
 */
export const useEntities = (params = {}, options = {}) => {
  const { skipCache = false, ...queryOptions } = options;

  return useQuery({
    queryKey: knowledgeQueryKeys.entities(params),
    queryFn: async () => {
      return requestCacheService.request(
        'knowledge.entities',
        params,
        async () => {
          const response = await apiClient.get('/api/v1/knowledge/entities', {
            params,
          });
          return response.data;
        },
        { skipCache }
      );
    },
    staleTime: 3 * 60 * 1000, // 3分钟
    cacheTime: 5 * 60 * 1000, // 5分钟
    ...queryOptions,
  });
};

/**
 * 使用带缓存的搜索查询
 */
export const useKnowledgeSearch = (query, options = {}) => {
  const { skipCache = false, ...queryOptions } = options;

  return useQuery({
    queryKey: knowledgeQueryKeys.search(query),
    queryFn: async () => {
      if (!query || query.trim().length < 2) return { results: [] };

      return requestCacheService.request(
        'knowledge.search',
        { query },
        async () => {
          const response = await apiClient.post('/api/v1/knowledge/search', {
            query,
          });
          return response.data;
        },
        { skipCache }
      );
    },
    enabled: !!query && query.trim().length >= 2,
    staleTime: 30 * 1000, // 30秒
    cacheTime: 2 * 60 * 1000, // 2分钟
    ...queryOptions,
  });
};

/**
 * 使用带缓存的统计信息查询
 */
export const useKnowledgeStats = (baseId, options = {}) => {
  const { skipCache = false, ...queryOptions } = options;

  return useQuery({
    queryKey: knowledgeQueryKeys.stats(baseId),
    queryFn: async () => {
      return requestCacheService.request(
        'knowledge.stats',
        { baseId },
        async () => {
          const response = await apiClient.get('/api/v1/knowledge/stats', {
            params: { baseId },
          });
          return response.data;
        },
        { skipCache }
      );
    },
    staleTime: 15 * 60 * 1000, // 15分钟
    cacheTime: 30 * 60 * 1000, // 30分钟
    ...queryOptions,
  });
};

/**
 * 使用带缓存的处理状态查询
 */
export const useProcessingStatus = (documentId, options = {}) => {
  return useQuery({
    queryKey: knowledgeQueryKeys.processing(documentId),
    queryFn: async () => {
      if (!documentId) return null;

      const response = await apiClient.get(
        `/api/v1/knowledge/documents/${documentId}/processing`
      );
      return response.data;
    },
    enabled: !!documentId,
    refetchInterval: 5000, // 每5秒刷新
    staleTime: 0, // 实时数据不缓存
    ...options,
  });
};

// ==================== Mutations ====================

/**
 * 创建文档 Mutation
 */
export const useCreateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/api/v1/knowledge/documents', data);
      return response.data;
    },
    onSuccess: () => {
      // 清除文档列表缓存
      queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.all,
      });
      requestCacheService.invalidatePattern('knowledge\\.documents');
    },
  });
};

/**
 * 更新文档 Mutation
 */
export const useUpdateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/api/v1/knowledge/documents/${id}`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      // 清除相关缓存
      queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.document(variables.id),
      });
      queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.documents(),
      });
      requestCacheService.invalidate('knowledge.document', { id: variables.id });
    },
  });
};

/**
 * 删除文档 Mutation
 */
export const useDeleteDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/api/v1/knowledge/documents/${id}`);
      return id;
    },
    onSuccess: (id) => {
      // 清除相关缓存
      queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.all,
      });
      requestCacheService.invalidate('knowledge.document', { id });
      requestCacheService.invalidatePattern('knowledge\\.documents');
    },
  });
};

/**
 * 批量删除文档 Mutation
 */
export const useBatchDeleteDocuments = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ids) => {
      const response = await apiClient.post('/api/v1/knowledge/documents/batch-delete', {
        ids,
      });
      return response.data;
    },
    onSuccess: () => {
      // 清除所有文档相关缓存
      queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.all,
      });
      requestCacheService.invalidatePattern('knowledge\\.');
    },
  });
};

// ==================== 缓存管理 Hooks ====================

/**
 * 使用缓存管理
 */
export const useCacheManager = () => {
  const queryClient = useQueryClient();

  const invalidateCache = useCallback((key, params) => {
    requestCacheService.invalidate(key, params);
  }, []);

  const invalidatePattern = useCallback((pattern) => {
    requestCacheService.invalidatePattern(pattern);
  }, []);

  const clearAllCache = useCallback(() => {
    requestCacheService.clear();
  }, []);

  const refreshQuery = useCallback((queryKey) => {
    queryClient.invalidateQueries({ queryKey });
  }, [queryClient]);

  const prefetchQuery = useCallback(
    async (queryKey, queryFn) => {
      await queryClient.prefetchQuery({
        queryKey,
        queryFn,
        staleTime: 5 * 60 * 1000,
      });
    },
    [queryClient]
  );

  const getCacheStats = useCallback(() => {
    return requestCacheService.getStats();
  }, []);

  return useMemo(
    () => ({
      invalidateCache,
      invalidatePattern,
      clearAllCache,
      refreshQuery,
      prefetchQuery,
      getCacheStats,
    }),
    [invalidateCache, invalidatePattern, clearAllCache, refreshQuery, prefetchQuery, getCacheStats]
  );
};

/**
 * 使用预加载
 */
export const usePrefetch = () => {
  const queryClient = useQueryClient();

  const prefetchDocument = useCallback(
    (id) => {
      if (!id) return;
      queryClient.prefetchQuery({
        queryKey: knowledgeQueryKeys.document(id),
        queryFn: async () => {
          const response = await apiClient.get(`/api/v1/knowledge/documents/${id}`);
          return response.data;
        },
        staleTime: 5 * 60 * 1000,
      });
    },
    [queryClient]
  );

  const prefetchDocuments = useCallback(
    (params = {}) => {
      queryClient.prefetchQuery({
        queryKey: knowledgeQueryKeys.documents(params),
        queryFn: async () => {
          const response = await apiClient.get('/api/v1/knowledge/documents', {
            params,
          });
          return response.data;
        },
        staleTime: 2 * 60 * 1000,
      });
    },
    [queryClient]
  );

  return useMemo(
    () => ({
      prefetchDocument,
      prefetchDocuments,
    }),
    [prefetchDocument, prefetchDocuments]
  );
};

// ==================== 乐观更新 Hooks ====================

/**
 * 使用乐观更新
 */
export const useOptimisticUpdate = () => {
  const queryClient = useQueryClient();

  const optimisticUpdate = useCallback(
    (queryKey, updater) => {
      // 取消正在进行的重新获取
      queryClient.cancelQueries({ queryKey });

      // 保存之前的值
      const previousValue = queryClient.getQueryData(queryKey);

      // 乐观更新
      queryClient.setQueryData(queryKey, updater);

      // 返回回滚函数
      return () => {
        queryClient.setQueryData(queryKey, previousValue);
      };
    },
    [queryClient]
  );

  return { optimisticUpdate };
};
