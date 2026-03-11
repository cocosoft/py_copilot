/**
 * 知识库状态选择器 Hooks - FE-002 状态管理优化
 *
 * 提供细粒度的状态订阅和派生状态计算
 *
 * @task FE-002
 * @phase 前端界面优化
 */

import { useCallback, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import useKnowledgeStore from '../stores/knowledgeStore';

// ==================== 基础选择器 ====================

/**
 * 使用知识库列表
 */
export const useKnowledgeBases = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      knowledgeBases: state.knowledgeBases,
      total: state.knowledgeBasesTotal,
      loading: state.knowledgeBasesLoading,
      error: state.knowledgeBasesError,
    }))
  );
};

/**
 * 使用当前知识库
 */
export const useCurrentKnowledgeBase = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      currentKnowledgeBase: state.currentKnowledgeBase,
      loading: state.currentKnowledgeBaseLoading,
      error: state.currentKnowledgeBaseError,
    }))
  );
};

/**
 * 使用文档列表
 */
export const useDocuments = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      documents: state.documents,
      total: state.documentsTotal,
      loading: state.documentsLoading,
      error: state.documentsError,
      page: state.documentsPage,
      pageSize: state.documentsPageSize,
    }))
  );
};

/**
 * 使用片段列表
 */
export const useChunks = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      chunks: state.chunks,
      total: state.chunksTotal,
      loading: state.chunksLoading,
      error: state.chunksError,
      page: state.chunksPage,
      pageSize: state.chunksPageSize,
    }))
  );
};

/**
 * 使用实体列表
 */
export const useEntities = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      entities: state.entities,
      total: state.entitiesTotal,
      loading: state.entitiesLoading,
      error: state.entitiesError,
    }))
  );
};

/**
 * 使用关系列表
 */
export const useRelationships = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      relationships: state.relationships,
      total: state.relationshipsTotal,
      loading: state.relationshipsLoading,
      error: state.relationshipsError,
    }))
  );
};

// ==================== 选择状态选择器 ====================

/**
 * 使用文档选择状态
 */
export const useDocumentSelection = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      selectedIds: state.selectedDocuments,
      selectedCount: state.selectedDocuments.length,
      isAllSelected:
        state.documents.length > 0 &&
        state.selectedDocuments.length === state.documents.length,
      isPartialSelected:
        state.selectedDocuments.length > 0 &&
        state.selectedDocuments.length < state.documents.length,
      toggleSelection: state.toggleDocumentSelection,
      setSelection: state.setSelectedDocuments,
      selectAll: state.selectAllDocuments,
      clearSelection: useCallback(() => state.setSelectedDocuments([]), [state]),
    }))
  );
};

/**
 * 使用片段选择状态
 */
export const useChunkSelection = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      selectedIds: state.selectedChunks,
      selectedCount: state.selectedChunks.length,
      expandedIds: state.expandedChunks,
      toggleSelection: state.toggleChunkSelection,
      setSelection: state.setSelectedChunks,
      toggleExpansion: state.toggleChunkExpansion,
      setExpanded: state.setExpandedChunks,
    }))
  );
};

// ==================== 过滤器选择器 ====================

/**
 * 使用文档过滤器
 */
export const useDocumentFilters = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      filters: state.documentFilters,
      setFilters: state.setDocumentFilters,
      resetFilters: state.resetDocumentFilters,
    }))
  );
};

/**
 * 使用片段过滤器
 */
export const useChunkFilters = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      filters: state.chunkFilters,
      setFilters: state.setChunkFilters,
      resetFilters: state.resetChunkFilters,
    }))
  );
};

/**
 * 使用实体过滤器
 */
export const useEntityFilters = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      filters: state.entityFilters,
      setFilters: state.setEntityFilters,
    }))
  );
};

// ==================== 搜索选择器 ====================

/**
 * 使用搜索状态
 */
export const useSearch = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      query: state.searchQuery,
      results: state.searchResults,
      loading: state.searchLoading,
      error: state.searchError,
      setQuery: state.setSearchQuery,
      setResults: state.setSearchResults,
      setLoading: state.setSearchLoading,
    }))
  );
};

// ==================== 视图选择器 ====================

/**
 * 使用视图状态
 */
export const useViewState = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      viewMode: state.viewMode,
      sidebarCollapsed: state.sidebarCollapsed,
      activeTab: state.activeTab,
      setViewMode: state.setViewMode,
      toggleSidebar: state.toggleSidebar,
      setActiveTab: state.setActiveTab,
    }))
  );
};

// ==================== 处理状态选择器 ====================

/**
 * 使用处理状态
 */
export const useProcessingStatus = (id) => {
  return useKnowledgeStore(
    useShallow((state) => ({
      status: state.processingStatus[id],
      progress: state.processingProgress[id],
      setStatus: (status) => state.setProcessingStatus(id, status),
      setProgress: (progress) => state.setProcessingProgress(id, progress),
      clear: () => state.clearProcessingStatus(id),
    }))
  );
};

/**
 * 使用批量操作状态
 */
export const useBatchOperation = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      operation: state.batchOperation,
      progress: state.batchProgress,
      results: state.batchResults,
      isRunning: !!state.batchOperation,
      start: state.startBatchOperation,
      updateProgress: state.updateBatchProgress,
      addResult: state.addBatchResult,
      end: state.endBatchOperation,
    }))
  );
};

// ==================== 派生状态选择器 ====================

/**
 * 使用过滤后的文档
 */
export const useFilteredDocuments = () => {
  return useKnowledgeStore((state) => {
    const { documents, documentFilters } = state;

    return useMemo(() => {
      let result = [...documents];

      // 搜索过滤
      if (documentFilters.search) {
        const searchLower = documentFilters.search.toLowerCase();
        result = result.filter(
          (doc) =>
            doc.title?.toLowerCase().includes(searchLower) ||
            doc.content?.toLowerCase().includes(searchLower)
        );
      }

      // 状态过滤
      if (documentFilters.status !== 'all') {
        result = result.filter((doc) => doc.status === documentFilters.status);
      }

      // 文件类型过滤
      if (documentFilters.fileType !== 'all') {
        result = result.filter((doc) => doc.fileType === documentFilters.fileType);
      }

      // 日期范围过滤
      if (documentFilters.dateRange) {
        const { start, end } = documentFilters.dateRange;
        result = result.filter((doc) => {
          const docDate = new Date(doc.updatedAt);
          return docDate >= start && docDate <= end;
        });
      }

      // 排序
      result.sort((a, b) => {
        const aVal = a[documentFilters.sortBy];
        const bVal = b[documentFilters.sortBy];
        const order = documentFilters.sortOrder === 'asc' ? 1 : -1;

        if (typeof aVal === 'string') {
          return aVal.localeCompare(bVal) * order;
        }
        return (aVal - bVal) * order;
      });

      return result;
    }, [documents, documentFilters]);
  });
};

/**
 * 使用文档统计
 */
export const useDocumentStats = () => {
  return useKnowledgeStore((state) => {
    const { documents } = state;

    return useMemo(() => {
      const stats = {
        total: documents.length,
        byStatus: {},
        byType: {},
        totalSize: 0,
        totalChunks: 0,
      };

      documents.forEach((doc) => {
        // 按状态统计
        stats.byStatus[doc.status] = (stats.byStatus[doc.status] || 0) + 1;

        // 按类型统计
        stats.byType[doc.fileType] = (stats.byType[doc.fileType] || 0) + 1;

        // 总大小
        stats.totalSize += doc.size || 0;

        // 总片段数
        stats.totalChunks += doc.chunkCount || 0;
      });

      return stats;
    }, [documents]);
  });
};

/**
 * 使用片段统计
 */
export const useChunkStats = () => {
  return useKnowledgeStore((state) => {
    const { chunks } = state;

    return useMemo(() => {
      const stats = {
        total: chunks.length,
        byStatus: {},
        avgLength: 0,
        totalTokens: 0,
      };

      let totalLength = 0;

      chunks.forEach((chunk) => {
        stats.byStatus[chunk.status] = (stats.byStatus[chunk.status] || 0) + 1;
        totalLength += chunk.content?.length || 0;
        stats.totalTokens += chunk.tokenCount || 0;
      });

      stats.avgLength = chunks.length > 0 ? Math.round(totalLength / chunks.length) : 0;

      return stats;
    }, [chunks]);
  });
};

// ==================== 组合选择器 ====================

/**
 * 使用知识库完整状态
 */
export const useKnowledgeState = () => {
  return useKnowledgeStore();
};

/**
 * 使用知识库 Actions
 */
export const useKnowledgeActions = () => {
  return useKnowledgeStore(
    useShallow((state) => ({
      // 设置方法
      setKnowledgeBases: state.setKnowledgeBases,
      setCurrentKnowledgeBase: state.setCurrentKnowledgeBase,
      setDocuments: state.setDocuments,
      appendDocuments: state.appendDocuments,
      setChunks: state.setChunks,
      appendChunks: state.appendChunks,
      setEntities: state.setEntities,
      setRelationships: state.setRelationships,

      // 选择方法
      toggleDocumentSelection: state.toggleDocumentSelection,
      setSelectedDocuments: state.setSelectedDocuments,
      selectAllDocuments: state.selectAllDocuments,
      clearSelection: state.clearSelection,
      toggleChunkSelection: state.toggleChunkSelection,
      setSelectedChunks: state.setSelectedChunks,
      toggleChunkExpansion: state.toggleChunkExpansion,
      setExpandedChunks: state.setExpandedChunks,

      // 过滤器方法
      setDocumentFilters: state.setDocumentFilters,
      resetDocumentFilters: state.resetDocumentFilters,
      setChunkFilters: state.setChunkFilters,
      resetChunkFilters: state.resetChunkFilters,
      setEntityFilters: state.setEntityFilters,

      // 分页方法
      setDocumentsPage: state.setDocumentsPage,
      setDocumentsPageSize: state.setDocumentsPageSize,
      setChunksPage: state.setChunksPage,

      // 搜索方法
      setSearchQuery: state.setSearchQuery,
      setSearchResults: state.setSearchResults,

      // 视图方法
      setViewMode: state.setViewMode,
      toggleSidebar: state.toggleSidebar,
      setActiveTab: state.setActiveTab,

      // 处理方法
      setProcessingStatus: state.setProcessingStatus,
      setProcessingProgress: state.setProcessingProgress,
      clearProcessingStatus: state.clearProcessingStatus,

      // 批量操作方法
      startBatchOperation: state.startBatchOperation,
      updateBatchProgress: state.updateBatchProgress,
      addBatchResult: state.addBatchResult,
      endBatchOperation: state.endBatchOperation,

      // 工具方法
      clearAllSelections: state.clearAllSelections,
      clearCache: state.clearCache,
      reset: state.reset,
    }))
  );
};

// ==================== 默认导出 ====================

const useKnowledge = () => {
  const state = useKnowledgeState();
  const actions = useKnowledgeActions();

  return {
    ...state,
    ...actions,
  };
};

export default useKnowledge;
