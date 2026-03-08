/**
 * 知识图谱React Hook
 * 
 * 提供知识图谱相关的状态和操作
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import knowledgeGraphApi from '../services/knowledgeGraphApi';

/**
 * 使用知识图谱构建任务
 * @param {string} knowledgeBaseId - 知识库ID
 * @returns {Object} 任务状态和操作
 */
export const useKnowledgeGraphBuild = (knowledgeBaseId) => {
  const [taskStatus, setTaskStatus] = useState(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const pollingRef = useRef(null);

  /**
   * 开始构建知识图谱
   * @param {string[]} documentIds - 文档ID列表
   * @param {Object} options - 构建选项
   */
  const startBuild = useCallback(async (documentIds, options = {}) => {
    if (!knowledgeBaseId || !documentIds?.length) {
      setError('知识库ID和文档ID不能为空');
      return;
    }

    setIsBuilding(true);
    setError(null);
    setProgress(0);

    try {
      const response = await knowledgeGraphApi.buildKnowledgeGraph(
        knowledgeBaseId,
        documentIds,
        options
      );

      if (response.task_id) {
        // 开始轮询任务状态
        startPolling(response.task_id);
      }
    } catch (err) {
      setError(err.message || '构建任务提交失败');
      setIsBuilding(false);
    }
  }, [knowledgeBaseId]);

  /**
   * 开始轮询任务状态
   * @param {string} taskId - 任务ID
   */
  const startPolling = useCallback((taskId) => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    pollingRef.current = setInterval(async () => {
      try {
        const status = await knowledgeGraphApi.getTaskStatus(taskId);
        setTaskStatus(status);
        setProgress(status.progress || 0);

        if (status.status === 'success' || status.status === 'failure') {
          clearInterval(pollingRef.current);
          setIsBuilding(false);
        }
      } catch (err) {
        console.error('获取任务状态失败:', err);
      }
    }, 1000);
  }, []);

  /**
   * 取消构建
   */
  const cancelBuild = useCallback(async () => {
    if (taskStatus?.task_id) {
      try {
        await knowledgeGraphApi.revokeTask(taskStatus.task_id);
        clearInterval(pollingRef.current);
        setIsBuilding(false);
      } catch (err) {
        console.error('取消任务失败:', err);
      }
    }
  }, [taskStatus]);

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  return {
    isBuilding,
    progress,
    taskStatus,
    error,
    startBuild,
    cancelBuild,
  };
};

/**
 * 使用知识图谱数据
 * @param {string} knowledgeBaseId - 知识库ID
 * @param {string} layer - 图层类型
 * @returns {Object} 图谱数据和状态
 */
export const useKnowledgeGraphData = (knowledgeBaseId, layer = 'document') => {
  const [graphData, setGraphData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * 加载图谱数据
   */
  const loadGraphData = useCallback(async () => {
    if (!knowledgeBaseId) return;

    setLoading(true);
    setError(null);

    try {
      const [data, statsData] = await Promise.all([
        knowledgeGraphApi.getGraphData(knowledgeBaseId, layer),
        knowledgeGraphApi.getGraphStats(knowledgeBaseId),
      ]);

      setGraphData(data);
      setStats(statsData);
    } catch (err) {
      setError(err.message || '加载图谱数据失败');
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, layer]);

  /**
   * 刷新数据
   */
  const refresh = useCallback(() => {
    loadGraphData();
  }, [loadGraphData]);

  // 自动加载
  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  return {
    graphData,
    stats,
    loading,
    error,
    refresh,
  };
};

/**
 * 使用实体搜索
 * @param {string} knowledgeBaseId - 知识库ID
 * @returns {Object} 搜索状态和结果
 */
export const useEntitySearch = (knowledgeBaseId) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const searchTimeoutRef = useRef(null);

  /**
   * 搜索实体
   * @param {string} query - 搜索关键词
   * @param {Object} options - 搜索选项
   */
  const search = useCallback(async (query, options = {}) => {
    if (!knowledgeBaseId || !query?.trim()) {
      setResults([]);
      return;
    }

    // 防抖处理
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await knowledgeGraphApi.searchEntities(
          knowledgeBaseId,
          query,
          options
        );
        setResults(response.results || []);
      } catch (err) {
        setError(err.message || '搜索失败');
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
  }, [knowledgeBaseId]);

  /**
   * 清除搜索结果
   */
  const clear = useCallback(() => {
    setResults([]);
    setError(null);
  }, []);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  return {
    results,
    loading,
    error,
    search,
    clear,
  };
};

/**
 * 使用实体提取任务
 * @param {string} knowledgeBaseId - 知识库ID
 * @returns {Object} 提取任务状态
 */
export const useEntityExtraction = (knowledgeBaseId) => {
  const [tasks, setTasks] = useState([]);
  const [isExtracting, setIsExtracting] = useState(false);

  /**
   * 提取单个文档
   * @param {string} documentId - 文档ID
   * @param {Object} options - 提取选项
   */
  const extractDocument = useCallback(async (documentId, options = {}) => {
    if (!knowledgeBaseId || !documentId) return;

    setIsExtracting(true);

    try {
      const response = await knowledgeGraphApi.extractEntities(
        documentId,
        knowledgeBaseId,
        options
      );

      setTasks(prev => [...prev, response]);
      return response;
    } catch (err) {
      console.error('提取失败:', err);
      throw err;
    } finally {
      setIsExtracting(false);
    }
  }, [knowledgeBaseId]);

  /**
   * 批量提取文档
   * @param {string[]} documentIds - 文档ID列表
   * @param {Object} options - 批量选项
   */
  const batchExtract = useCallback(async (documentIds, options = {}) => {
    if (!knowledgeBaseId || !documentIds?.length) return;

    setIsExtracting(true);

    try {
      const response = await knowledgeGraphApi.batchExtractEntities(
        documentIds,
        knowledgeBaseId,
        options
      );

      setTasks(prev => [...prev, response]);
      return response;
    } catch (err) {
      console.error('批量提取失败:', err);
      throw err;
    } finally {
      setIsExtracting(false);
    }
  }, [knowledgeBaseId]);

  return {
    tasks,
    isExtracting,
    extractDocument,
    batchExtract,
  };
};

/**
 * 使用任务列表
 * @returns {Object} 任务列表状态
 */
export const useTaskList = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * 加载任务列表
   * @param {Object} params - 查询参数
   */
  const loadTasks = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);

    try {
      const response = await knowledgeGraphApi.getTaskList(params);
      setTasks(response.tasks || []);
    } catch (err) {
      setError(err.message || '加载任务列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 取消任务
   * @param {string} taskId - 任务ID
   */
  const cancelTask = useCallback(async (taskId) => {
    try {
      await knowledgeGraphApi.revokeTask(taskId);
      // 刷新任务列表
      loadTasks();
    } catch (err) {
      console.error('取消任务失败:', err);
    }
  }, [loadTasks]);

  return {
    tasks,
    loading,
    error,
    loadTasks,
    cancelTask,
  };
};

export default {
  useKnowledgeGraphBuild,
  useKnowledgeGraphData,
  useEntitySearch,
  useEntityExtraction,
  useTaskList,
};
