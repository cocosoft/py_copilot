/**
 * 实体识别管理页面
 *
 * 用于管理实体识别任务，包括：
 * - 查看所有识别任务
 * - 查看任务进度和状态
 * - 批量重新识别文档
 * - 查看失败记录
 *
 * @task 大文件实体识别改造方案
 * @phase 阶段四 - 管理功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { FiRefreshCw, FiPlay, FiCheckCircle, FiXCircle, FiClock, FiFilter, FiPause, FiSquare } from 'react-icons/fi';
import { getExtractionTasks, reExtractAllChunks, pauseExtractionTask, resumeExtractionTask, cancelExtractionTask } from '../../utils/api/hierarchyApi';
import { useNotification } from '../../hooks/useNotification';
import './EntityExtractionManager.css';

/**
 * 实体识别管理组件
 *
 * @param {Object} props - 组件属性
 * @param {string|number} props.knowledgeBaseId - 知识库ID
 * @param {Function} props.onStatsUpdate - 统计更新回调函数
 */
const EntityExtractionManager = ({ knowledgeBaseId, onStatsUpdate }) => {
  // 状态
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState('');
  const [taskTypeFilter, setTaskTypeFilter] = useState('');
  const [processingDocId, setProcessingDocId] = useState(null);

  // 通知钩子
  const { showNotification } = useNotification();

  /**
   * 检查是否有正在处理中的任务
   */
  const hasProcessingTasks = useCallback(() => {
    return tasks.some(task => task.status === 'processing' || task.status === 'pending');
  }, [tasks]);

  /**
   * 加载任务列表
   */
  const loadTasks = useCallback(async (options = {}) => {
    if (!knowledgeBaseId) return;

    const { skipStatsUpdate = false } = options;
    setLoading(true);
    try {
      const response = await getExtractionTasks(knowledgeBaseId, {
        status: statusFilter,
        taskType: taskTypeFilter,
        page,
        pageSize
      });

      if (response.code === 200) {
        const newTasks = response.data?.list || [];
        const newTotal = response.data?.total || 0;

        // 检查是否需要刷新层级统计
        // 条件：1. 不是跳过更新 2. 有更新回调 3. 任务状态或实体数量发生变化
        if (!skipStatsUpdate && onStatsUpdate) {
          const shouldUpdateStats = checkStatsNeedUpdate(tasks, newTasks);
          if (shouldUpdateStats) {
            onStatsUpdate();
          }
        }

        setTasks(newTasks);
        setTotal(newTotal);
      } else {
        showNotification({
          type: 'error',
          message: response.message || '加载任务列表失败'
        });
      }
    } catch (error) {
      console.error('加载任务列表失败:', error);
      showNotification({
        type: 'error',
        message: '加载任务列表失败: ' + (error.message || '未知错误')
      });
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [knowledgeBaseId, statusFilter, taskTypeFilter, page, pageSize, onStatsUpdate]);

  /**
   * 检查是否需要更新层级统计
   * 当任务完成或实体数量变化时返回 true
   */
  const checkStatsNeedUpdate = (oldTasks, newTasks) => {
    if (oldTasks.length === 0 && newTasks.length > 0) return true;
    if (oldTasks.length !== newTasks.length) return true;

    const oldTaskMap = new Map(oldTasks.map(t => [t.id, t]));

    for (const newTask of newTasks) {
      const oldTask = oldTaskMap.get(newTask.id);
      if (!oldTask) return true;

      // 任务状态从 processing 变为 completed/failed
      if (oldTask.status === 'processing' && (newTask.status === 'completed' || newTask.status === 'failed')) {
        return true;
      }

      // 实体数量发生变化
      if (oldTask.chunk_entity_count !== newTask.chunk_entity_count ||
          oldTask.document_entity_count !== newTask.document_entity_count) {
        return true;
      }
    }

    return false;
  };

  // 初始加载和筛选变化时重新加载
  useEffect(() => {
    if (knowledgeBaseId) {
      loadTasks();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [knowledgeBaseId, statusFilter, taskTypeFilter, page, pageSize]);

  // 自动轮询：当有处理中的任务时，每3秒刷新一次
  useEffect(() => {
    if (!knowledgeBaseId) return;

    let intervalId = null;

    if (hasProcessingTasks()) {
      intervalId = setInterval(() => {
        // 轮询时跳过统计更新，由 checkStatsNeedUpdate 判断是否需要更新
        loadTasks({ skipStatsUpdate: false });
      }, 3000); // 每3秒刷新一次
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [knowledgeBaseId, tasks]);

  /**
   * 处理重新识别全部片段
   */
  const handleReExtractAll = useCallback(async (documentId) => {
    if (!documentId) return;

    setProcessingDocId(documentId);
    try {
      const response = await reExtractAllChunks(knowledgeBaseId, documentId);

      if (response.code === 200) {
        showNotification({
          type: 'success',
          message: `任务创建成功！共 ${response.data?.total_chunks} 个片段待处理`
        });
        // 刷新列表 - 直接调用而不是通过依赖
        loadTasks();
      } else {
        showNotification({
          type: 'error',
          message: response.message || '创建任务失败'
        });
      }
    } catch (error) {
      console.error('创建重新识别任务失败:', error);
      showNotification({
        type: 'error',
        message: '创建任务失败: ' + (error.message || '未知错误')
      });
    } finally {
      setProcessingDocId(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [knowledgeBaseId]);

  /**
   * 处理暂停任务
   */
  const handlePauseTask = useCallback(async (taskId) => {
    try {
      const response = await pauseExtractionTask(knowledgeBaseId, taskId);
      if (response.code === 200) {
        showNotification({
          type: 'success',
          message: `任务已暂停，当前进度: ${response.data?.progress?.percentage}%`
        });
        loadTasks();
      } else {
        showNotification({
          type: 'error',
          message: response.message || '暂停任务失败'
        });
      }
    } catch (error) {
      console.error('暂停任务失败:', error);
      showNotification({
        type: 'error',
        message: '暂停任务失败: ' + (error.message || '未知错误')
      });
    }
  }, [knowledgeBaseId, loadTasks, showNotification]);

  /**
   * 处理恢复任务
   */
  const handleResumeTask = useCallback(async (taskId) => {
    try {
      const response = await resumeExtractionTask(knowledgeBaseId, taskId);
      if (response.code === 200) {
        showNotification({
          type: 'success',
          message: '任务已恢复，继续处理中'
        });
        loadTasks();
      } else {
        showNotification({
          type: 'error',
          message: response.message || '恢复任务失败'
        });
      }
    } catch (error) {
      console.error('恢复任务失败:', error);
      showNotification({
        type: 'error',
        message: '恢复任务失败: ' + (error.message || '未知错误')
      });
    }
  }, [knowledgeBaseId, loadTasks, showNotification]);

  /**
   * 处理取消任务
   */
  const handleCancelTask = useCallback(async (taskId) => {
    if (!window.confirm('确定要取消此任务吗？已处理的结果将被保留。')) {
      return;
    }

    try {
      const response = await cancelExtractionTask(knowledgeBaseId, taskId);
      if (response.code === 200) {
        showNotification({
          type: 'success',
          message: `任务已取消，已保留 ${response.data?.preserved_entities?.chunk_entities || 0} 个片段级实体`
        });
        loadTasks();
      } else {
        showNotification({
          type: 'error',
          message: response.message || '取消任务失败'
        });
      }
    } catch (error) {
      console.error('取消任务失败:', error);
      showNotification({
        type: 'error',
        message: '取消任务失败: ' + (error.message || '未知错误')
      });
    }
  }, [knowledgeBaseId, loadTasks, showNotification]);

  /**
   * 获取状态显示配置
   */
  const getStatusConfig = (status) => {
    const configs = {
      pending: { icon: <FiClock />, text: '待处理', className: 'status-pending' },
      processing: { icon: <FiRefreshCw className="spinning" />, text: '处理中', className: 'status-processing' },
      paused: { icon: <FiPause />, text: '已暂停', className: 'status-paused' },
      completed: { icon: <FiCheckCircle />, text: '已完成', className: 'status-completed' },
      failed: { icon: <FiXCircle />, text: '失败', className: 'status-failed' }
    };
    return configs[status] || configs.pending;
  };

  /**
   * 获取任务类型显示文本
   */
  const getTaskTypeText = (type) => {
    const types = {
      full: '全文档识别',
      incremental: '增量识别',
      retry: '重试识别'
    };
    return types[type] || type;
  };

  // 计算总页数
  const totalPages = Math.ceil(total / pageSize);

  // 如果没有知识库ID，显示提示
  if (!knowledgeBaseId) {
    return (
      <div className="entity-extraction-manager">
        <div className="eem-header">
          <h2>实体识别任务管理</h2>
        </div>
        <div className="eem-empty">
          <span className="empty-icon">📚</span>
          <span>请先选择一个知识库</span>
        </div>
      </div>
    );
  }

  return (
    <div className="entity-extraction-manager">
      {/* 头部 */}
      <div className="eem-header">
        <h2>实体识别任务管理</h2>
        <button
          className="refresh-btn"
          onClick={loadTasks}
          disabled={loading}
        >
          <FiRefreshCw className={loading ? 'spinning' : ''} />
          <span>刷新</span>
        </button>
      </div>

      {/* 筛选栏 */}
      <div className="eem-filters">
        <div className="filter-row">
          <FiFilter className="filter-icon" />
          <div className="filter-group">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              title="筛选任务状态"
            >
              <option value="">所有状态</option>
              <option value="pending">待处理</option>
              <option value="processing">处理中</option>
              <option value="paused">已暂停</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
            </select>
          </div>
          <div className="filter-group">
            <select
              value={taskTypeFilter}
              onChange={(e) => setTaskTypeFilter(e.target.value)}
              title="筛选任务类型：全文档识别-完整识别；增量识别-仅识别新增内容；重试识别-重新识别失败文档"
            >
              <option value="">所有类型</option>
              <option value="full">全文档识别</option>
              <option value="incremental">增量识别</option>
              <option value="retry">重试识别</option>
            </select>
          </div>
        </div>
        {/* 任务类型说明 */}
        <div className="filter-help">
          <span className="help-icon" title="任务类型说明：&#10;• 全文档识别：对文档进行完整的实体识别&#10;• 增量识别：仅识别新增或修改的内容&#10;• 重试识别：对之前识别失败的文档重新识别">ℹ️</span>
        </div>
      </div>

      {/* 任务列表 */}
      <div className="eem-task-list">
        {loading && tasks.length === 0 ? (
          <div className="eem-loading">
            <div className="loading-spinner"></div>
            <span>加载中...</span>
          </div>
        ) : tasks.length === 0 ? (
          <div className="eem-empty">
            <span className="empty-icon">📋</span>
            <span>暂无识别任务</span>
          </div>
        ) : (
          <>
            <table className="eem-table">
              <thead>
                <tr>
                  <th>文档</th>
                  <th>状态</th>
                  <th>类型</th>
                  <th>进度</th>
                  <th>实体统计</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => {
                  const statusConfig = getStatusConfig(task.status);
                  return (
                    <tr key={task.id}>
                      <td className="doc-title" title={task.document_title}>
                        {task.document_title}
                      </td>
                      <td>
                        <span className={`status-badge ${statusConfig.className}`}>
                          {statusConfig.icon}
                          {statusConfig.text}
                        </span>
                      </td>
                      <td>{getTaskTypeText(task.task_type)}</td>
                      <td>
                        <div className="progress-cell">
                          <div className="progress-bar">
                            <div
                              className={`progress-fill ${task.status === 'processing' ? 'progress-animated' : ''}`}
                              style={{ width: `${task.progress}%` }}
                            ></div>
                          </div>
                          <div className="progress-details">
                            <span className="progress-percentage">{task.progress.toFixed(1)}%</span>
                            <span className="progress-chunks" title="已处理片段数/总片段数">
                              片段: {task.processed_chunks}/{task.total_chunks}
                            </span>
                            {task.status === 'processing' && task.total_chunks > 0 && (
                              <span className="progress-remaining">
                                剩余: {task.total_chunks - task.processed_chunks}个
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="stats-cell">
                          <span>片段级: {task.chunk_entity_count}</span>
                          <span>文档级: {task.document_entity_count}</span>
                        </div>
                      </td>
                      <td>
                        {task.created_at
                          ? new Date(task.created_at).toLocaleString()
                          : '-'}
                      </td>
                      <td>
                        <div className="action-buttons">
                          {/* 处理中任务：显示暂停和取消按钮 */}
                          {task.status === 'processing' && (
                            <>
                              <button
                                className="action-btn pause-btn"
                                onClick={() => handlePauseTask(task.id)}
                                title="暂停任务"
                              >
                                <FiPause />
                                <span>暂停</span>
                              </button>
                              <button
                                className="action-btn cancel-btn"
                                onClick={() => handleCancelTask(task.id)}
                                title="取消任务"
                              >
                                <FiSquare />
                                <span>取消</span>
                              </button>
                            </>
                          )}

                          {/* 已暂停任务：显示恢复和取消按钮 */}
                          {task.status === 'paused' && (
                            <>
                              <button
                                className="action-btn resume-btn"
                                onClick={() => handleResumeTask(task.id)}
                                title="恢复任务"
                              >
                                <FiPlay />
                                <span>恢复</span>
                              </button>
                              <button
                                className="action-btn cancel-btn"
                                onClick={() => handleCancelTask(task.id)}
                                title="取消任务"
                              >
                                <FiSquare />
                                <span>取消</span>
                              </button>
                            </>
                          )}

                          {/* 已完成/失败任务：显示重新识别按钮 */}
                          {(task.status === 'completed' || task.status === 'failed') && (
                            <button
                              className="action-btn"
                              onClick={() => handleReExtractAll(task.document_id)}
                              disabled={processingDocId === task.document_id}
                              title="重新识别所有片段"
                            >
                              {processingDocId === task.document_id ? (
                                <span className="loading-icon">⏳</span>
                              ) : (
                                <FiPlay />
                              )}
                              <span>重新识别</span>
                            </button>
                          )}

                          {/* 待处理任务：显示取消按钮 */}
                          {task.status === 'pending' && (
                            <button
                              className="action-btn cancel-btn"
                              onClick={() => handleCancelTask(task.id)}
                              title="取消任务"
                            >
                              <FiSquare />
                              <span>取消</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* 分页 */}
            {totalPages > 1 && (
              <div className="eem-pagination">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  上一页
                </button>
                <span className="page-info">
                  第 {page} 页 / 共 {totalPages} 页 (共 {total} 条)
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* 统计摘要 */}
      {tasks.length > 0 && (
        <div className="eem-summary">
          <div className="summary-item">
            <span className="summary-label">总任务数:</span>
            <span className="summary-value">{total}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">处理中:</span>
            <span className="summary-value">
              {tasks.filter(t => t.status === 'processing').length}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">已暂停:</span>
            <span className="summary-value" style={{ color: '#fa8c16' }}>
              {tasks.filter(t => t.status === 'paused').length}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">已完成:</span>
            <span className="summary-value">
              {tasks.filter(t => t.status === 'completed').length}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">失败:</span>
            <span className="summary-value">
              {tasks.filter(t => t.status === 'failed').length}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default EntityExtractionManager;
