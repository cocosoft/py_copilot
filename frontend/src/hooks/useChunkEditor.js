/**
 * 片段编辑器 Hooks - FE-007 交互式片段编辑器
 *
 * 提供片段编辑相关的数据获取和操作功能
 *
 * @task FE-007
 * @phase 前端功能拓展
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useMemo, useRef } from 'react';
import apiClient from '../services/apiClient';
import { queryKeys } from '../config/queryClient';

/**
 * 使用文档片段查询
 *
 * @param {string} documentId - 文档ID
 * @param {Object} options - 查询选项
 * @returns {Object} 查询结果
 */
export const useDocumentChunks = (documentId, options = {}) => {
  const { enabled = true } = options;

  return useQuery({
    queryKey: queryKeys.knowledge.chunks(documentId),
    queryFn: async () => {
      if (!documentId) return null;

      const response = await apiClient.get(
        `/api/v1/knowledge/documents/${documentId}/chunks`
      );
      return response.data;
    },
    enabled: !!documentId && enabled,
    staleTime: 2 * 60 * 1000, // 2分钟
  });
};

/**
 * 使用片段详情查询
 *
 * @param {string} chunkId - 片段ID
 * @returns {Object} 查询结果
 */
export const useChunkDetail = (chunkId) => {
  return useQuery({
    queryKey: [...queryKeys.knowledge.all, 'chunk', chunkId],
    queryFn: async () => {
      if (!chunkId) return null;

      const response = await apiClient.get(`/api/v1/knowledge/chunks/${chunkId}`);
      return response.data;
    },
    enabled: !!chunkId,
  });
};

/**
 * 使用更新片段 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useUpdateChunk = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ chunkId, data }) => {
      const response = await apiClient.put(`/api/v1/knowledge/chunks/${chunkId}`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      // 清除相关缓存
      queryClient.invalidateQueries({
        queryKey: queryKeys.knowledge.chunks(),
      });
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.knowledge.all, 'chunk', variables.chunkId],
      });
    },
  });
};

/**
 * 使用批量更新片段 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useBatchUpdateChunks = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ documentId, chunks }) => {
      const response = await apiClient.put(
        `/api/v1/knowledge/documents/${documentId}/chunks`,
        { chunks }
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.knowledge.chunks(variables.documentId),
      });
    },
  });
};

/**
 * 使用删除片段 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useDeleteChunk = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (chunkId) => {
      await apiClient.delete(`/api/v1/knowledge/chunks/${chunkId}`);
      return chunkId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.knowledge.chunks(),
      });
    },
  });
};

/**
 * 使用分割片段 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useSplitChunk = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ chunkId, position }) => {
      const response = await apiClient.post(`/api/v1/knowledge/chunks/${chunkId}/split`, {
        position,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.knowledge.chunks(),
      });
    },
  });
};

/**
 * 使用合并片段 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useMergeChunks = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ chunkId1, chunkId2 }) => {
      const response = await apiClient.post('/api/v1/knowledge/chunks/merge', {
        chunkId1,
        chunkId2,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.knowledge.chunks(),
      });
    },
  });
};

/**
 * 使用编辑器历史记录
 *
 * @param {Array} initialChunks - 初始片段
 * @returns {Object} 历史记录状态和操作
 */
export const useEditorHistory = (initialChunks = []) => {
  const [history, setHistory] = useState([JSON.parse(JSON.stringify(initialChunks))]);
  const [historyIndex, setHistoryIndex] = useState(0);

  /**
   * 保存状态到历史
   */
  const saveState = useCallback((chunks) => {
    setHistory((prev) => {
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push(JSON.parse(JSON.stringify(chunks)));
      // 限制历史记录数量
      if (newHistory.length > 50) {
        newHistory.shift();
      }
      return newHistory;
    });
    setHistoryIndex((prev) => Math.min(prev + 1, 49));
  }, [historyIndex]);

  /**
   * 撤销
   */
  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      return JSON.parse(JSON.stringify(history[newIndex]));
    }
    return null;
  }, [history, historyIndex]);

  /**
   * 重做
   */
  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      return JSON.parse(JSON.stringify(history[newIndex]));
    }
    return null;
  }, [history, historyIndex]);

  /**
   * 是否可以撤销
   */
  const canUndo = historyIndex > 0;

  /**
   * 是否可以重做
   */
  const canRedo = historyIndex < history.length - 1;

  /**
   * 重置历史
   */
  const resetHistory = useCallback((chunks) => {
    setHistory([JSON.parse(JSON.stringify(chunks))]);
    setHistoryIndex(0);
  }, []);

  return useMemo(
    () => ({
      history,
      historyIndex,
      canUndo,
      canRedo,
      saveState,
      undo,
      redo,
      resetHistory,
    }),
    [history, historyIndex, canUndo, canRedo, saveState, undo, redo, resetHistory]
  );
};

/**
 * 使用片段选择
 *
 * @returns {Object} 选择状态和操作
 */
export const useChunkSelection = () => {
  const [selectedIds, setSelectedIds] = useState([]);
  const [activeId, setActiveId] = useState(null);

  /**
   * 选择片段
   */
  const selectChunk = useCallback((chunkId) => {
    setActiveId(chunkId);
    setSelectedIds((prev) => {
      if (prev.includes(chunkId)) {
        return prev.filter((id) => id !== chunkId);
      }
      return [...prev, chunkId];
    });
  }, []);

  /**
   * 设置活动片段
   */
  const setActiveChunk = useCallback((chunkId) => {
    setActiveId(chunkId);
  }, []);

  /**
   * 选择范围
   */
  const selectRange = useCallback((startId, endId, allChunks) => {
    const startIndex = allChunks.findIndex((c) => c.id === startId);
    const endIndex = allChunks.findIndex((c) => c.id === endId);

    if (startIndex === -1 || endIndex === -1) return;

    const [min, max] = startIndex < endIndex ? [startIndex, endIndex] : [endIndex, startIndex];
    const rangeIds = allChunks.slice(min, max + 1).map((c) => c.id);

    setSelectedIds((prev) => [...new Set([...prev, ...rangeIds])]);
  }, []);

  /**
   * 全选
   */
  const selectAll = useCallback((allChunks) => {
    setSelectedIds(allChunks.map((c) => c.id));
  }, []);

  /**
   * 清空选择
   */
  const clearSelection = useCallback(() => {
    setSelectedIds([]);
    setActiveId(null);
  }, []);

  /**
   * 检查是否选中
   */
  const isSelected = useCallback(
    (chunkId) => selectedIds.includes(chunkId),
    [selectedIds]
  );

  return useMemo(
    () => ({
      selectedIds,
      activeId,
      selectChunk,
      setActiveChunk,
      selectRange,
      selectAll,
      clearSelection,
      isSelected,
    }),
    [selectedIds, activeId, selectChunk, setActiveChunk, selectRange, selectAll, clearSelection, isSelected]
  );
};

/**
 * 使用片段编辑
 *
 * @param {Object} chunk - 片段
 * @returns {Object} 编辑状态和操作
 */
export const useChunkEdit = (chunk) => {
  const [content, setContent] = useState(chunk?.content || '');
  const [errors, setErrors] = useState([]);

  /**
   * 验证内容
   */
  const validate = useCallback(() => {
    const newErrors = [];

    if (!content || content.trim().length === 0) {
      newErrors.push('内容不能为空');
    }

    if (content.length > 10000) {
      newErrors.push('内容长度不能超过10000字符');
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  }, [content]);

  /**
   * 获取元数据
   */
  const getMetadata = useCallback(() => {
    return {
      wordCount: content.length,
      charCount: content.length,
      lineCount: content.split('\n').length,
    };
  }, [content]);

  return useMemo(
    () => ({
      content,
      setContent,
      errors,
      validate,
      getMetadata,
      isValid: errors.length === 0,
    }),
    [content, errors, validate, getMetadata]
  );
};

/**
 * 使用片段操作
 *
 * @param {Array} chunks - 片段数组
 * @param {Function} setChunks - 设置片段函数
 * @returns {Object} 操作函数
 */
export const useChunkOperations = (chunks, setChunks) => {
  /**
   * 更新片段
   */
  const updateChunk = useCallback(
    (chunkId, updates) => {
      setChunks((prev) =>
        prev.map((chunk) =>
          chunk.id === chunkId
            ? { ...chunk, ...updates, updatedAt: new Date().toISOString() }
            : chunk
        )
      );
    },
    [setChunks]
  );

  /**
   * 分割片段
   */
  const splitChunk = useCallback(
    (chunkId, position) => {
      const chunkIndex = chunks.findIndex((c) => c.id === chunkId);
      if (chunkIndex === -1) return;

      const chunk = chunks[chunkIndex];
      const beforeContent = chunk.content.slice(0, position);
      const afterContent = chunk.content.slice(position);

      if (beforeContent.trim().length === 0 || afterContent.trim().length === 0) {
        return;
      }

      const newChunk = {
        id: `chunk-${Date.now()}`,
        content: afterContent,
        startIndex: chunk.startIndex + position,
        endIndex: chunk.endIndex,
        metadata: {
          wordCount: afterContent.length,
          charCount: afterContent.length,
          entityCount: 0,
          quality: chunk.metadata?.quality || 0.8,
        },
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      const updatedChunk = {
        ...chunk,
        content: beforeContent,
        endIndex: chunk.startIndex + position,
        metadata: {
          ...chunk.metadata,
          wordCount: beforeContent.length,
          charCount: beforeContent.length,
        },
        updatedAt: new Date().toISOString(),
      };

      const newChunks = [
        ...chunks.slice(0, chunkIndex),
        updatedChunk,
        newChunk,
        ...chunks.slice(chunkIndex + 1),
      ];

      // 重新计算索引
      let currentIndex = 0;
      newChunks.forEach((c) => {
        c.startIndex = currentIndex;
        c.endIndex = currentIndex + c.content.length;
        currentIndex = c.endIndex;
      });

      setChunks(newChunks);
    },
    [chunks, setChunks]
  );

  /**
   * 合并片段
   */
  const mergeChunks = useCallback(
    (chunkId1, chunkId2) => {
      const index1 = chunks.findIndex((c) => c.id === chunkId1);
      const index2 = chunks.findIndex((c) => c.id === chunkId2);

      if (index1 === -1 || index2 === -1 || Math.abs(index1 - index2) !== 1) {
        return;
      }

      const [firstIndex, secondIndex] = index1 < index2 ? [index1, index2] : [index2, index1];
      const firstChunk = chunks[firstIndex];
      const secondChunk = chunks[secondIndex];

      const mergedContent = firstChunk.content + secondChunk.content;
      const mergedChunk = {
        ...firstChunk,
        content: mergedContent,
        endIndex: firstChunk.startIndex + mergedContent.length,
        metadata: {
          ...firstChunk.metadata,
          wordCount: mergedContent.length,
          charCount: mergedContent.length,
          entityCount: (firstChunk.metadata?.entityCount || 0) + (secondChunk.metadata?.entityCount || 0),
        },
        updatedAt: new Date().toISOString(),
      };

      const newChunks = [
        ...chunks.slice(0, firstIndex),
        mergedChunk,
        ...chunks.slice(secondIndex + 1),
      ];

      // 重新计算索引
      let currentIndex = 0;
      newChunks.forEach((c) => {
        c.startIndex = currentIndex;
        c.endIndex = currentIndex + c.content.length;
        currentIndex = c.endIndex;
      });

      setChunks(newChunks);
    },
    [chunks, setChunks]
  );

  /**
   * 删除片段
   */
  const deleteChunk = useCallback(
    (chunkId) => {
      const newChunks = chunks.filter((c) => c.id !== chunkId);

      // 重新计算索引
      let currentIndex = 0;
      newChunks.forEach((c) => {
        c.startIndex = currentIndex;
        c.endIndex = currentIndex + c.content.length;
        currentIndex = c.endIndex;
      });

      setChunks(newChunks);
    },
    [chunks, setChunks]
  );

  /**
   * 批量删除
   */
  const batchDelete = useCallback(
    (chunkIds) => {
      const idSet = new Set(chunkIds);
      const newChunks = chunks.filter((c) => !idSet.has(c.id));

      // 重新计算索引
      let currentIndex = 0;
      newChunks.forEach((c) => {
        c.startIndex = currentIndex;
        c.endIndex = currentIndex + c.content.length;
        currentIndex = c.endIndex;
      });

      setChunks(newChunks);
    },
    [chunks, setChunks]
  );

  return useMemo(
    () => ({
      updateChunk,
      splitChunk,
      mergeChunks,
      deleteChunk,
      batchDelete,
    }),
    [updateChunk, splitChunk, mergeChunks, deleteChunk, batchDelete]
  );
};

/**
 * 使用完整的片段编辑器
 *
 * @param {string} documentId - 文档ID
 * @returns {Object} 完整的编辑器状态
 */
export const useChunkEditor = (documentId) => {
  const { data: initialChunks, isLoading, error } = useDocumentChunks(documentId);
  const [chunks, setChunks] = useState([]);
  const [hasChanges, setHasChanges] = useState(false);

  // 同步初始数据
  useState(() => {
    if (initialChunks) {
      setChunks(initialChunks);
    }
  });

  // 历史记录
  const history = useEditorHistory(chunks);

  // 选择
  const selection = useChunkSelection();

  // 操作
  const operations = useChunkOperations(chunks, setChunks);

  // Mutations
  const updateChunkMutation = useUpdateChunk();
  const batchUpdateMutation = useBatchUpdateChunks();
  const deleteChunkMutation = useDeleteChunk();
  const splitChunkMutation = useSplitChunk();
  const mergeChunksMutation = useMergeChunks();

  /**
   * 保存更改
   */
  const saveChanges = useCallback(async () => {
    if (!documentId || !hasChanges) return;

    await batchUpdateMutation.mutateAsync({
      documentId,
      chunks,
    });

    setHasChanges(false);
    history.resetHistory(chunks);
  }, [documentId, hasChanges, chunks, batchUpdateMutation, history]);

  /**
   * 更新片段并保存历史
   */
  const updateChunkWithHistory = useCallback(
    (chunkId, updates) => {
      operations.updateChunk(chunkId, updates);
      history.saveState(chunks);
      setHasChanges(true);
    },
    [operations, history, chunks]
  );

  /**
   * 分割片段并保存历史
   */
  const splitChunkWithHistory = useCallback(
    (chunkId, position) => {
      operations.splitChunk(chunkId, position);
      history.saveState(chunks);
      setHasChanges(true);
    },
    [operations, history, chunks]
  );

  /**
   * 合并片段并保存历史
   */
  const mergeChunksWithHistory = useCallback(
    (chunkId1, chunkId2) => {
      operations.mergeChunks(chunkId1, chunkId2);
      history.saveState(chunks);
      setHasChanges(true);
    },
    [operations, history, chunks]
  );

  /**
   * 删除片段并保存历史
   */
  const deleteChunkWithHistory = useCallback(
    (chunkId) => {
      operations.deleteChunk(chunkId);
      history.saveState(chunks);
      setHasChanges(true);
    },
    [operations, history, chunks]
  );

  /**
   * 撤销
   */
  const undo = useCallback(() => {
    const previousState = history.undo();
    if (previousState) {
      setChunks(previousState);
      setHasChanges(true);
    }
  }, [history]);

  /**
   * 重做
   */
  const redo = useCallback(() => {
    const nextState = history.redo();
    if (nextState) {
      setChunks(nextState);
      setHasChanges(true);
    }
  }, [history]);

  // 统计信息
  const stats = useMemo(() => {
    return {
      totalChunks: chunks.length,
      totalChars: chunks.reduce((sum, c) => sum + (c.content?.length || 0), 0),
      totalWords: chunks.reduce((sum, c) => sum + (c.metadata?.wordCount || 0), 0),
      avgQuality: chunks.length > 0
        ? (chunks.reduce((sum, c) => sum + (c.metadata?.quality || 0), 0) / chunks.length).toFixed(2)
        : 0,
    };
  }, [chunks]);

  return useMemo(
    () => ({
      // 数据
      chunks,
      isLoading,
      error,
      stats,
      hasChanges,

      // 历史
      canUndo: history.canUndo,
      canRedo: history.canRedo,

      // 选择
      selection,

      // 操作
      updateChunk: updateChunkWithHistory,
      splitChunk: splitChunkWithHistory,
      mergeChunks: mergeChunksWithHistory,
      deleteChunk: deleteChunkWithHistory,
      batchDelete: operations.batchDelete,

      // 历史操作
      undo,
      redo,
      saveChanges,

      // 加载状态
      isSaving: batchUpdateMutation.isPending,
    }),
    [
      chunks,
      isLoading,
      error,
      stats,
      hasChanges,
      history,
      selection,
      updateChunkWithHistory,
      splitChunkWithHistory,
      mergeChunksWithHistory,
      deleteChunkWithHistory,
      operations.batchDelete,
      undo,
      redo,
      saveChanges,
      batchUpdateMutation.isPending,
    ]
  );
};

// ==================== 工具函数 ====================

/**
 * 计算片段统计信息
 *
 * @param {Object} chunk - 片段
 * @returns {Object} 统计信息
 */
export const calculateChunkStats = (chunk) => {
  const content = chunk.content || '';

  return {
    charCount: content.length,
    wordCount: content.trim().split(/\s+/).filter(Boolean).length,
    lineCount: content.split('\n').length,
    paragraphCount: content.split('\n\n').filter(Boolean).length,
  };
};

/**
 * 验证片段内容
 *
 * @param {string} content - 内容
 * @returns {Object} 验证结果
 */
export const validateChunkContent = (content) => {
  const errors = [];
  const warnings = [];

  if (!content || content.trim().length === 0) {
    errors.push('内容不能为空');
  }

  if (content.length > 10000) {
    errors.push('内容长度不能超过10000字符');
  }

  if (content.length < 50) {
    warnings.push('内容较短，建议合并到相邻片段');
  }

  if (content.length > 2000) {
    warnings.push('内容较长，建议分割成多个片段');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
};

/**
 * 查找最佳分割位置
 *
 * @param {string} content - 内容
 * @param {number} targetPosition - 目标位置
 * @returns {number} 最佳分割位置
 */
export const findBestSplitPosition = (content, targetPosition) => {
  // 优先在句子结束处分割
  const sentenceEndings = ['。', '！', '？', '.', '!', '?'];

  // 向前查找
  for (let i = targetPosition; i > targetPosition - 50 && i > 0; i--) {
    if (sentenceEndings.includes(content[i - 1])) {
      return i;
    }
  }

  // 向后查找
  for (let i = targetPosition; i < targetPosition + 50 && i < content.length; i++) {
    if (sentenceEndings.includes(content[i - 1])) {
      return i;
    }
  }

  // 在空白字符处分割
  for (let i = targetPosition; i > targetPosition - 30 && i > 0; i--) {
    if (/\s/.test(content[i - 1])) {
      return i;
    }
  }

  return targetPosition;
};

/**
 * 生成片段预览
 *
 * @param {string} content - 内容
 * @param {number} maxLength - 最大长度
 * @returns {string} 预览文本
 */
export const generateChunkPreview = (content, maxLength = 100) => {
  if (content.length <= maxLength) {
    return content;
  }

  return content.slice(0, maxLength) + '...';
};
