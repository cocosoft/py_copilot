/**
 * 批量处理 Hooks - FE-005 批量处理向导
 *
 * 提供批量处理相关的数据获取和操作功能
 *
 * @task FE-005
 * @phase 前端功能拓展
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useRef, useMemo } from 'react';
import apiClient from '../services/apiClient';
import { queryKeys } from '../config/queryClient';

/**
 * 使用批量处理 Mutation
 *
 * @returns {Object} Mutation 结果
 */
export const useBatchProcess = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ documentIds, config }) => {
      const response = await apiClient.post('/api/v1/knowledge/batch-process', {
        documentIds,
        config,
      });
      return response.data;
    },
    onSuccess: () => {
      // 清除相关缓存
      queryClient.invalidateQueries({
        queryKey: queryKeys.knowledge,
      });
    },
  });
};

/**
 * 使用带进度跟踪的批量处理
 *
 * @returns {Object} 批量处理状态和操作
 */
export const useBatchProcessingWithProgress = () => {
  const [progress, setProgress] = useState({
    current: 0,
    total: 0,
    percentage: 0,
    currentDocument: '',
  });
  const [status, setStatus] = useState('idle'); // idle, processing, completed, error, cancelled
  const [results, setResults] = useState(null);
  const abortControllerRef = useRef(null);

  const batchProcessMutation = useBatchProcess();

  /**
   * 开始批量处理
   */
  const startProcessing = useCallback(async (documentIds, config, callbacks = {}) => {
    const { onProgress, onComplete, onError } = callbacks;

    setStatus('processing');
    setProgress({
      current: 0,
      total: documentIds.length,
      percentage: 0,
      currentDocument: '',
    });

    abortControllerRef.current = new AbortController();

    try {
      // 使用 EventSource 或 WebSocket 获取实时进度
      // 这里使用模拟进度更新
      for (let i = 0; i < documentIds.length; i++) {
        if (abortControllerRef.current.signal.aborted) {
          throw new Error('Cancelled');
        }

        // 模拟处理延迟
        await new Promise((resolve) => setTimeout(resolve, 500));

        const progressUpdate = {
          current: i + 1,
          total: documentIds.length,
          percentage: Math.round(((i + 1) / documentIds.length) * 100),
          currentDocument: `文档 ${documentIds[i]}`,
        };

        setProgress(progressUpdate);
        onProgress?.(progressUpdate);
      }

      // 执行实际的批量处理请求
      const result = await batchProcessMutation.mutateAsync({
        documentIds,
        config,
      });

      setResults(result);
      setStatus('completed');
      onComplete?.(result);

      return result;
    } catch (error) {
      if (error.message === 'Cancelled') {
        setStatus('cancelled');
      } else {
        setStatus('error');
        onError?.(error);
      }
      throw error;
    }
  }, [batchProcessMutation]);

  /**
   * 取消处理
   */
  const cancelProcessing = useCallback(() => {
    abortControllerRef.current?.abort();
    setStatus('cancelled');
  }, []);

  /**
   * 重置状态
   */
  const reset = useCallback(() => {
    setStatus('idle');
    setProgress({
      current: 0,
      total: 0,
      percentage: 0,
      currentDocument: '',
    });
    setResults(null);
  }, []);

  return useMemo(
    () => ({
      progress,
      status,
      results,
      isProcessing: status === 'processing',
      isCompleted: status === 'completed',
      isError: status === 'error',
      isCancelled: status === 'cancelled',
      startProcessing,
      cancelProcessing,
      reset,
    }),
    [progress, status, results, startProcessing, cancelProcessing, reset]
  );
};

/**
 * 使用批量处理配置
 *
 * @param {Object} initialConfig - 初始配置
 * @returns {Object} 配置状态和操作
 */
export const useBatchProcessingConfig = (initialConfig = {}) => {
  const [config, setConfig] = useState({
    processingMode: 'standard',
    chunkStrategy: 'semantic',
    chunkSize: 1024,
    overlapSize: 128,
    extractEntities: true,
    extractRelationships: false,
    generateSummaries: false,
    skipExisting: false,
    ...initialConfig,
  });

  /**
   * 更新配置项
   */
  const updateConfig = useCallback((key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  }, []);

  /**
   * 批量更新配置
   */
  const updateMultipleConfig = useCallback((updates) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  }, []);

  /**
   * 重置配置
   */
  const resetConfig = useCallback(() => {
    setConfig({
      processingMode: 'standard',
      chunkStrategy: 'semantic',
      chunkSize: 1024,
      overlapSize: 128,
      extractEntities: true,
      extractRelationships: false,
      generateSummaries: false,
      skipExisting: false,
      ...initialConfig,
    });
  }, [initialConfig]);

  /**
   * 验证配置
   */
  const validateConfig = useCallback(() => {
    const errors = [];

    if (config.chunkSize < 256) {
      errors.push('分块大小不能小于 256 字符');
    }

    if (config.chunkSize > 4096) {
      errors.push('分块大小不能大于 4096 字符');
    }

    if (config.overlapSize >= config.chunkSize) {
      errors.push('重叠大小必须小于分块大小');
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }, [config]);

  return useMemo(
    () => ({
      config,
      updateConfig,
      updateMultipleConfig,
      resetConfig,
      validateConfig,
    }),
    [config, updateConfig, updateMultipleConfig, resetConfig, validateConfig]
  );
};

/**
 * 使用文档选择
 *
 * @param {Array} documents - 文档列表
 * @returns {Object} 选择状态和操作
 */
export const useDocumentSelection = (documents = []) => {
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({ status: 'all', type: 'all' });

  // 过滤后的文档
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      if (searchQuery && !doc.title?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      if (filters.status !== 'all' && doc.status !== filters.status) {
        return false;
      }
      if (filters.type !== 'all' && doc.fileType !== filters.type) {
        return false;
      }
      return true;
    });
  }, [documents, searchQuery, filters]);

  // 选择/取消选择
  const toggleSelection = useCallback((docId) => {
    setSelectedIds((prev) =>
      prev.includes(docId)
        ? prev.filter((id) => id !== docId)
        : [...prev, docId]
    );
  }, []);

  // 全选
  const selectAll = useCallback(() => {
    const filteredIds = filteredDocuments.map((doc) => doc.id);
    setSelectedIds((prev) => [...new Set([...prev, ...filteredIds])]);
  }, [filteredDocuments]);

  // 取消全选
  const deselectAll = useCallback(() => {
    const filteredIds = new Set(filteredDocuments.map((doc) => doc.id));
    setSelectedIds((prev) => prev.filter((id) => !filteredIds.has(id)));
  }, [filteredDocuments]);

  // 全选切换
  const toggleSelectAll = useCallback((checked) => {
    if (checked) {
      selectAll();
    } else {
      deselectAll();
    }
  }, [selectAll, deselectAll]);

  // 清空选择
  const clearSelection = useCallback(() => {
    setSelectedIds([]);
  }, []);

  // 选择统计
  const selectionStats = useMemo(() => ({
    selectedCount: selectedIds.length,
    totalCount: documents.length,
    filteredCount: filteredDocuments.length,
    isAllSelected: filteredDocuments.length > 0 &&
      filteredDocuments.every((doc) => selectedIds.includes(doc.id)),
    isPartialSelected: filteredDocuments.some((doc) => selectedIds.includes(doc.id)) &&
      !filteredDocuments.every((doc) => selectedIds.includes(doc.id)),
  }), [selectedIds, documents, filteredDocuments]);

  return useMemo(
    () => ({
      selectedIds,
      filteredDocuments,
      searchQuery,
      filters,
      selectionStats,
      setSearchQuery,
      setFilters,
      toggleSelection,
      selectAll,
      deselectAll,
      toggleSelectAll,
      clearSelection,
    }),
    [
      selectedIds,
      filteredDocuments,
      searchQuery,
      filters,
      selectionStats,
      toggleSelection,
      selectAll,
      deselectAll,
      toggleSelectAll,
      clearSelection,
    ]
  );
};

/**
 * 使用批量处理结果
 *
 * @param {Object} results - 处理结果
 * @returns {Object} 结果统计和操作
 */
export const useBatchProcessingResults = (results = null) => {
  const [filter, setFilter] = useState('all');

  // 过滤后的结果
  const filteredResults = useMemo(() => {
    if (!results?.details) return [];
    if (filter === 'all') return results.details;
    return results.details.filter((r) => r.status === filter);
  }, [results, filter]);

  // 统计信息
  const stats = useMemo(() => {
    if (!results) return null;

    return {
      total: results.total || 0,
      success: results.success || 0,
      failed: results.failed || 0,
      skipped: results.skipped || 0,
      successRate: results.total
        ? ((results.success / results.total) * 100).toFixed(1)
        : 0,
      averageProcessingTime: results.details?.length
        ? (
            results.details.reduce((sum, r) => sum + (parseFloat(r.processingTime) || 0), 0) /
            results.details.length
          ).toFixed(1)
        : 0,
    };
  }, [results]);

  // 下载报告
  const downloadReport = useCallback(() => {
    if (!results) return;

    const report = {
      timestamp: new Date().toISOString(),
      summary: stats,
      details: results.details,
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch-processing-report-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [results, stats]);

  // 导出 CSV
  const exportCSV = useCallback(() => {
    if (!results?.details) return;

    const headers = ['文档ID', '文档名称', '状态', '处理时间', '错误信息'];
    const rows = results.details.map((r) => [
      r.id,
      r.documentName,
      r.status,
      r.processingTime,
      r.error || '',
    ]);

    const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch-processing-results-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [results]);

  return useMemo(
    () => ({
      filteredResults,
      stats,
      filter,
      setFilter,
      downloadReport,
      exportCSV,
    }),
    [filteredResults, stats, filter, downloadReport, exportCSV]
  );
};

/**
 * 使用完整的批量处理流程
 *
 * @returns {Object} 完整的批量处理流程
 */
export const useBatchProcessingFlow = () => {
  const [step, setStep] = useState(0); // 0: select, 1: configure, 2: process, 3: preview
  const processing = useBatchProcessingWithProgress();
  const config = useBatchProcessingConfig();

  // 下一步
  const nextStep = useCallback(() => {
    setStep((prev) => Math.min(prev + 1, 3));
  }, []);

  // 上一步
  const prevStep = useCallback(() => {
    setStep((prev) => Math.max(prev - 1, 0));
  }, []);

  // 跳转到指定步骤
  const goToStep = useCallback((stepIndex) => {
    setStep(stepIndex);
  }, []);

  // 重置流程
  const reset = useCallback(() => {
    setStep(0);
    processing.reset();
    config.resetConfig();
  }, [processing, config]);

  // 开始处理
  const startProcessing = useCallback(
    async (documentIds, callbacks = {}) => {
      const validation = config.validateConfig();
      if (!validation.isValid) {
        throw new Error(validation.errors.join(', '));
      }

      setStep(2);
      await processing.startProcessing(documentIds, config.config, callbacks);
      setStep(3);
    },
    [processing, config]
  );

  return useMemo(
    () => ({
      step,
      stepInfo: {
        current: step,
        total: 4,
        isFirst: step === 0,
        isLast: step === 3,
      },
      processing,
      config,
      nextStep,
      prevStep,
      goToStep,
      reset,
      startProcessing,
    }),
    [step, processing, config, nextStep, prevStep, goToStep, reset, startProcessing]
  );
};

// ==================== 工具函数 ====================

/**
 * 生成处理配置预设
 *
 * @param {string} preset - 预设名称
 * @returns {Object} 配置对象
 */
export const getProcessingPreset = (preset) => {
  const presets = {
    standard: {
      processingMode: 'standard',
      chunkStrategy: 'semantic',
      chunkSize: 1024,
      overlapSize: 128,
      extractEntities: true,
      extractRelationships: false,
      generateSummaries: false,
    },
    quality: {
      processingMode: 'quality',
      chunkStrategy: 'semantic',
      chunkSize: 512,
      overlapSize: 64,
      extractEntities: true,
      extractRelationships: true,
      generateSummaries: true,
    },
    speed: {
      processingMode: 'speed',
      chunkStrategy: 'fixed',
      chunkSize: 2048,
      overlapSize: 256,
      extractEntities: false,
      extractRelationships: false,
      generateSummaries: false,
    },
  };

  return presets[preset] || presets.standard;
};

/**
 * 计算预估处理时间
 *
 * @param {number} documentCount - 文档数量
 * @param {Object} config - 处理配置
 * @returns {number} 预估时间（秒）
 */
export const estimateProcessingTime = (documentCount, config) => {
  const baseTime = 2; // 基础处理时间（秒/文档）
  const modeMultiplier = {
    standard: 1,
    quality: 2,
    speed: 0.5,
  };

  const featureTime =
    (config.extractEntities ? 1 : 0) +
    (config.extractRelationships ? 1.5 : 0) +
    (config.generateSummaries ? 1 : 0);

  return Math.round(documentCount * baseTime * (modeMultiplier[config.processingMode] || 1) + featureTime);
};
