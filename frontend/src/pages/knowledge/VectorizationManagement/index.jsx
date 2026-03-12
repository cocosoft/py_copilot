/**
 * 向量化管理页面
 * 
 * 管理文档的向量化处理任务
 */

import React, { useEffect, useCallback, useState } from 'react';
import { FiPlay, FiPause, FiRotateCcw, FiTrash2, FiSettings, FiBarChart2 } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { VirtualListEnhanced } from '../../../components/UI';
import { message } from '../../../components/UI/Message/Message';
import './styles.css';

/**
 * 任务状态配置
 */
const taskStatusConfig = {
  pending: {
    text: '等待中',
    color: '#8c8c8c',
    bgColor: '#f5f5f5',
  },
  processing: {
    text: '处理中',
    color: '#1890ff',
    bgColor: '#e6f7ff',
  },
  completed: {
    text: '已完成',
    color: '#52c41a',
    bgColor: '#f6ffed',
  },
  failed: {
    text: '失败',
    color: '#ff4d4f',
    bgColor: '#fff2f0',
  },
  paused: {
    text: '已暂停',
    color: '#faad14',
    bgColor: '#fffbe6',
  },
};

/**
 * 向量化管理页面
 */
const VectorizationManagement = () => {
  const { 
    currentKnowledgeBase,
    processingQueue,
    isProcessing,
    processingProgress,
    addToProcessingQueue,
    removeFromProcessingQueue,
    clearProcessingQueue,
    startProcessing,
    pauseProcessing,
    resumeProcessing,
  } = useKnowledgeStore();

  // 本地状态
  const [tasks, setTasks] = useState([]);
  const [selectedTasks, setSelectedTasks] = useState([]);
  const [showConfig, setShowConfig] = useState(false);
  const [config, setConfig] = useState({
    chunkSize: 1000,
    overlap: 200,
    embeddingModel: 'text-embedding-3-small',
  });

  /**
   * 获取任务列表
   */
  const fetchTasks = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      // TODO: 替换为实际 API 调用
      // const response = await knowledgeApi.getProcessingTasks(currentKnowledgeBase.id);
      
      // 模拟数据
      const mockTasks = Array.from({ length: 30 }, (_, i) => ({
        id: `task-${i}`,
        documentId: `doc-${i}`,
        documentName: `文档 ${i + 1}.pdf`,
        status: ['pending', 'processing', 'completed', 'failed'][Math.floor(Math.random() * 4)],
        progress: Math.floor(Math.random() * 100),
        createdAt: new Date(Date.now() - Math.random() * 86400000),
        completedAt: Math.random() > 0.5 ? new Date() : null,
        error: Math.random() > 0.8 ? '处理超时' : null,
      }));

      setTasks(mockTasks);
    } catch (error) {
      message.error({ content: '获取任务列表失败：' + error.message });
    }
  }, [currentKnowledgeBase]);

  // 初始加载
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  /**
   * 处理任务选择
   */
  const toggleTaskSelection = (taskId) => {
    setSelectedTasks(prev => 
      prev.includes(taskId) 
        ? prev.filter(id => id !== taskId)
        : [...prev, taskId]
    );
  };

  /**
   * 全选/取消全选
   */
  const toggleSelectAll = () => {
    if (selectedTasks.length === tasks.length) {
      setSelectedTasks([]);
    } else {
      setSelectedTasks(tasks.map(t => t.id));
    }
  };

  /**
   * 开始处理
   */
  const handleStart = () => {
    if (selectedTasks.length === 0) {
      message.warning({ content: '请先选择要处理的文档' });
      return;
    }
    startProcessing();
    message.success({ content: '开始处理选中的文档' });
  };

  /**
   * 暂停处理
   */
  const handlePause = () => {
    pauseProcessing();
    message.info({ content: '已暂停处理' });
  };

  /**
   * 重试失败任务
   */
  const handleRetry = () => {
    const failedTasks = tasks.filter(t => t.status === 'failed' && selectedTasks.includes(t.id));
    if (failedTasks.length === 0) {
      message.warning({ content: '请选择失败的任务' });
      return;
    }
    // TODO: 实现重试逻辑
    message.success({ content: `已重试 ${failedTasks.length} 个任务` });
  };

  /**
   * 删除任务
   */
  const handleDelete = () => {
    if (selectedTasks.length === 0) {
      message.warning({ content: '请先选择要删除的任务' });
      return;
    }
    // TODO: 实现删除逻辑
    setTasks(prev => prev.filter(t => !selectedTasks.includes(t.id)));
    setSelectedTasks([]);
    message.success({ content: `已删除 ${selectedTasks.length} 个任务` });
  };

  /**
   * 渲染任务项
   */
  const renderTask = useCallback((task, index) => {
    const status = taskStatusConfig[task.status];
    const isSelected = selectedTasks.includes(task.id);

    return (
      <div 
        key={task.id} 
        className={`task-item ${isSelected ? 'selected' : ''}`}
      >
        <div className="task-checkbox">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => toggleTaskSelection(task.id)}
          />
        </div>

        <div className="task-info">
          <h4 className="task-name">{task.documentName}</h4>
          <p className="task-meta">
            创建时间: {new Date(task.createdAt).toLocaleString()}
          </p>
        </div>

        <div className="task-progress">
          {task.status === 'processing' && (
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${task.progress}%` }}
              />
            </div>
          )}
          <span className="progress-text">{task.progress}%</span>
        </div>

        <div className="task-status">
          <span 
            className="status-badge"
            style={{
              color: status.color,
              backgroundColor: status.bgColor,
            }}
          >
            {status.text}
          </span>
        </div>

        {task.error && (
          <div className="task-error" title={task.error}>
            ⚠️
          </div>
        )}
      </div>
    );
  }, [selectedTasks]);

  // 统计信息
  const stats = {
    total: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    processing: tasks.filter(t => t.status === 'processing').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
  };

  if (!currentKnowledgeBase) {
    return (
      <div className="vectorization-empty">
        <div className="empty-icon">⚙️</div>
        <h3>请选择一个知识库</h3>
        <p>从左侧边栏选择一个知识库管理向量化任务</p>
      </div>
    );
  }

  return (
    <div className="vectorization-management">
      {/* 统计卡片 */}
      <div className="stats-cards">
        <div className="stat-card">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">总任务</span>
        </div>
        <div className="stat-card pending">
          <span className="stat-value">{stats.pending}</span>
          <span className="stat-label">等待中</span>
        </div>
        <div className="stat-card processing">
          <span className="stat-value">{stats.processing}</span>
          <span className="stat-label">处理中</span>
        </div>
        <div className="stat-card completed">
          <span className="stat-value">{stats.completed}</span>
          <span className="stat-label">已完成</span>
        </div>
        <div className="stat-card failed">
          <span className="stat-value">{stats.failed}</span>
          <span className="stat-label">失败</span>
        </div>
      </div>

      {/* 工具栏 */}
      <div className="vectorization-toolbar">
        <div className="toolbar-left">
          <input
            type="checkbox"
            checked={selectedTasks.length === tasks.length && tasks.length > 0}
            onChange={toggleSelectAll}
          />
          <span className="selection-info">
            已选择 {selectedTasks.length} 个任务
          </span>
        </div>

        <div className="toolbar-right">
          {isProcessing ? (
            <Button
              variant="secondary"
              icon={<FiPause />}
              onClick={handlePause}
            >
              暂停
            </Button>
          ) : (
            <Button
              variant="primary"
              icon={<FiPlay />}
              onClick={handleStart}
              disabled={selectedTasks.length === 0}
            >
              开始处理
            </Button>
          )}

          <Button
            variant="secondary"
            icon={<FiRotateCcw />}
            onClick={handleRetry}
            disabled={selectedTasks.length === 0}
          >
            重试
          </Button>

          <Button
            variant="danger"
            icon={<FiTrash2 />}
            onClick={handleDelete}
            disabled={selectedTasks.length === 0}
          >
            删除
          </Button>

          <Button
            variant="ghost"
            icon={<FiSettings />}
            onClick={() => setShowConfig(!showConfig)}
          >
            配置
          </Button>
        </div>
      </div>

      {/* 配置面板 */}
      {showConfig && (
        <div className="config-panel">
          <h4>处理配置</h4>
          <div className="config-form">
            <div className="config-item">
              <label>分块大小</label>
              <input
                type="number"
                value={config.chunkSize}
                onChange={(e) => setConfig({ ...config, chunkSize: parseInt(e.target.value) })}
              />
            </div>
            <div className="config-item">
              <label>重叠大小</label>
              <input
                type="number"
                value={config.overlap}
                onChange={(e) => setConfig({ ...config, overlap: parseInt(e.target.value) })}
              />
            </div>
            <div className="config-item">
              <label>嵌入模型</label>
              <select
                value={config.embeddingModel}
                onChange={(e) => setConfig({ ...config, embeddingModel: e.target.value })}
              >
                <option value="text-embedding-3-small">text-embedding-3-small</option>
                <option value="text-embedding-3-large">text-embedding-3-large</option>
                <option value="text-embedding-ada-002">text-embedding-ada-002</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* 任务列表 */}
      <div className="tasks-list-container">
        <VirtualListEnhanced
          items={tasks}
          renderItem={renderTask}
          estimateSize={72}
          overscan={10}
          emptyText={
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>暂无任务</h3>
              <p>选择文档开始向量化处理</p>
            </div>
          }
        />
      </div>
    </div>
  );
};

export default VectorizationManagement;
