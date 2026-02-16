import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import taskApi from '../../services/taskApi';
import TaskCreateModal from './TaskCreateModal';
import TaskDetailModal from './TaskDetailModal';
import TaskFilter from './TaskFilter';

function TaskList() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [filter, setFilter] = useState({
    status: '',
    keyword: ''
  });

  useEffect(() => {
    loadTasks();
  }, [filter]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const data = await taskApi.getTasks(filter);
      setTasks(data);
    } catch (error) {
      console.error('加载任务失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async (taskData) => {
    try {
      await taskApi.createTask(taskData);
      setShowCreateModal(false);
      loadTasks();
    } catch (error) {
      console.error('创建任务失败:', error);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (window.confirm('确定要删除这个任务吗？')) {
      try {
        await taskApi.deleteTask(taskId);
        loadTasks();
      } catch (error) {
        console.error('删除任务失败:', error);
      }
    }
  };

  const handleExecuteTask = async (taskId) => {
    try {
      await taskApi.executeTask(taskId);
      loadTasks();
    } catch (error) {
      console.error('执行任务失败:', error);
    }
  };

  const handleViewDetail = (task) => {
    setSelectedTask(task);
    setShowDetailModal(true);
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

  return (
    <div className="task-list">
      <div className="task-list-header">
        <h2>任务列表</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          创建任务
        </button>
      </div>

      <TaskFilter
        filter={filter}
        onFilterChange={setFilter}
      />

      {loading ? (
        <div className="loading-state">加载中...</div>
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <p>暂无任务</p>
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            创建第一个任务
          </button>
        </div>
      ) : (
        <div className="task-grid">
          {tasks.map((task) => (
            <motion.div
              key={task.id}
              className="task-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="task-card-header">
                <h3 className="task-title">{task.title}</h3>
                <div className="task-badges">
                  <span className={`badge ${getStatusColor(task.status)}`}>
                    {getStatusText(task.status)}
                  </span>
                  <span className={`badge ${getPriorityColor(task.priority)}`}>
                    {getPriorityText(task.priority)}
                  </span>
                </div>
              </div>

              {task.description && (
                <p className="task-description">{task.description}</p>
              )}

              {task.task_type && (
                <div className="task-info">
                  <span className="task-info-label">类型:</span>
                  <span className="task-info-value">{task.task_type}</span>
                </div>
              )}

              {task.complexity && (
                <div className="task-info">
                  <span className="task-info-label">复杂度:</span>
                  <span className="task-info-value">{task.complexity}</span>
                </div>
              )}

              {task.execution_time_ms && (
                <div className="task-info">
                  <span className="task-info-label">执行时间:</span>
                  <span className="task-info-value">
                    {(task.execution_time_ms / 1000).toFixed(2)}s
                  </span>
                </div>
              )}

              <div className="task-card-footer">
                <div className="task-time">
                  创建于: {new Date(task.created_at).toLocaleString('zh-CN')}
                </div>
                <div className="task-actions">
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleViewDetail(task)}
                  >
                    详情
                  </button>
                  {task.status === 'pending' && (
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => handleExecuteTask(task.id)}
                    >
                      执行
                    </button>
                  )}
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleDeleteTask(task.id)}
                  >
                    删除
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <TaskCreateModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateTask}
        />
      )}

      {showDetailModal && selectedTask && (
        <TaskDetailModal
          task={selectedTask}
          onClose={() => setShowDetailModal(false)}
          onExecute={handleExecuteTask}
          onDelete={handleDeleteTask}
        />
      )}
    </div>
  );
}

export default TaskList;
