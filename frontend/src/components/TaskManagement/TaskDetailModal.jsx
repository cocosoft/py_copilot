import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import taskApi from '../../services/taskApi';

function TaskDetailModal({ task, onClose, onExecute, onDelete }) {
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState(task);

  useEffect(() => {
    setCurrentTask(task);
  }, [task]);

  useEffect(() => {
    if (currentTask && (currentTask.status === 'analyzing' || currentTask.status === 'running')) {
      loadProgress();
      // 优化轮询频率：改为5秒轮询一次
      const interval = setInterval(loadProgress, 5000);
      return () => clearInterval(interval);
    }
  }, [currentTask]);

  const loadProgress = async () => {
    try {
      setLoading(true);
      const data = await taskApi.getTaskProgress(currentTask.id);
      setProgress(data);
      
      // 如果任务已完成或失败，停止轮询
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
        // 更新任务状态
        setCurrentTask({
          ...currentTask,
          status: data.status
        });
        return;
      }
    } catch (error) {
      console.error('加载任务进度失败:', error);
      // 如果加载失败，不继续轮询
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-gray-100 text-gray-800',
      analyzing: 'bg-blue-100 text-blue-800',
      running: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      pending: '待处理',
      analyzing: '分析中',
      running: '执行中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消'
    };
    return texts[status] || status;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'text-green-600',
      medium: 'text-yellow-600',
      high: 'text-red-600'
    };
    return colors[priority] || 'text-gray-600';
  };

  const getPriorityText = (priority) => {
    const texts = {
      low: '低',
      medium: '中',
      high: '高'
    };
    return texts[priority] || priority;
  };

  const handleExecute = () => {
    onExecute(currentTask.id);
    onClose();
  };

  const handleDelete = () => {
    if (window.confirm('确定要删除这个任务吗？')) {
      onDelete(currentTask.id);
      onClose();
    }
  };

  const handleCancel = async () => {
    try {
      await taskApi.cancelTask(currentTask.id);
      onClose();
    } catch (error) {
      console.error('取消任务失败:', error);
    }
  };

  if (!currentTask) return null;

  return (
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="modal-content modal-large"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>任务详情</h2>
          <button
            className="modal-close"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="task-detail-section">
            <h3>基本信息</h3>
            <div className="task-detail-row">
              <span className="task-detail-label">标题:</span>
              <span className="task-detail-value">{currentTask.title}</span>
            </div>
            <div className="task-detail-row">
              <span className="task-detail-label">状态:</span>
              <span className={`badge ${getStatusColor(currentTask.status)}`}>
                {getStatusText(currentTask.status)}
              </span>
            </div>
            <div className="task-detail-row">
              <span className="task-detail-label">优先级:</span>
              <span className={`badge ${getPriorityColor(currentTask.priority)}`}>
                {getPriorityText(currentTask.priority)}
              </span>
            </div>
            {currentTask.task_type && (
              <div className="task-detail-row">
                <span className="task-detail-label">类型:</span>
                <span className="task-detail-value">{currentTask.task_type}</span>
              </div>
            )}
            {currentTask.complexity && (
              <div className="task-detail-row">
                <span className="task-detail-label">复杂度:</span>
                <span className="task-detail-value">{currentTask.complexity}</span>
              </div>
            )}
          </div>

          {currentTask.description && (
            <div className="task-detail-section">
              <h3>任务描述</h3>
              <p className="task-detail-description">{currentTask.description}</p>
            </div>
          )}

          {(currentTask.status === 'analyzing' || currentTask.status === 'running') && progress && (
            <div className="task-detail-section">
              <h3>执行进度</h3>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress.progress}%` }}
                />
              </div>
              <div className="progress-text">
                {progress.completed_skills} / {progress.total_skills} 个技能已完成
              </div>
            </div>
          )}

          {currentTask.execution_time_ms && (
            <div className="task-detail-section">
              <h3>执行信息</h3>
              <div className="task-detail-row">
                <span className="task-detail-label">执行时间:</span>
                <span className="task-detail-value">
                  {(currentTask.execution_time_ms / 1000).toFixed(2)} 秒
                </span>
              </div>
              {currentTask.started_at && (
                <div className="task-detail-row">
                  <span className="task-detail-label">开始时间:</span>
                  <span className="task-detail-value">
                    {new Date(currentTask.started_at).toLocaleString('zh-CN')}
                  </span>
                </div>
              )}
              {currentTask.completed_at && (
                <div className="task-detail-row">
                  <span className="task-detail-label">完成时间:</span>
                  <span className="task-detail-value">
                    {new Date(currentTask.completed_at).toLocaleString('zh-CN')}
                  </span>
                </div>
              )}
            </div>
          )}

          {currentTask.error_message && (
            <div className="task-detail-section">
              <h3>错误信息</h3>
              <div className="error-box">
                {currentTask.error_message}
              </div>
            </div>
          )}

          {currentTask.output_data && (
            <div className="task-detail-section">
              <h3>执行结果</h3>
              <pre className="task-detail-output">
                {currentTask.output_data}
              </pre>
            </div>
          )}

          <div className="task-detail-section">
            <h3>时间信息</h3>
            <div className="task-detail-row">
              <span className="task-detail-label">创建时间:</span>
              <span className="task-detail-value">
                {new Date(currentTask.created_at).toLocaleString('zh-CN')}
              </span>
            </div>
            <div className="task-detail-row">
              <span className="task-detail-label">更新时间:</span>
              <span className="task-detail-value">
                {new Date(currentTask.updated_at).toLocaleString('zh-CN')}
              </span>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="btn btn-secondary"
            onClick={onClose}
          >
            关闭
          </button>
          {currentTask.status === 'pending' && (
            <button
              className="btn btn-primary"
              onClick={handleExecute}
            >
              执行任务
            </button>
          )}
          {(currentTask.status === 'analyzing' || currentTask.status === 'running') && (
            <button
              className="btn btn-warning"
              onClick={handleCancel}
            >
              取消任务
            </button>
          )}
          <button
            className="btn btn-danger"
            onClick={handleDelete}
          >
            删除任务
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default TaskDetailModal;
