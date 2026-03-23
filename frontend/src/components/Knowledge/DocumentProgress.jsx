/**
 * 文档进度追踪组件
 * 
 * 用于显示文档处理的详细进度，包括进度条和阶段列表
 */

import React from 'react';
import DocumentStatusBadge from './DocumentStatusBadge';
import './DocumentProgress.css';

/**
 * 处理阶段配置
 */
const PROCESSING_STAGES = [
  {
    key: 'text_extracted',
    label: '文本提取',
    icon: '📝',
    weight: 20,
    description: '从文档中提取文本内容'
  },
  {
    key: 'chunked',
    label: '切片处理',
    icon: '✂️',
    weight: 20,
    description: '将文本分割成适合向量化的片段'
  },
  {
    key: 'entity_extracted',
    label: '实体识别',
    icon: '🏷️',
    weight: 20,
    description: '识别文档中的命名实体'
  },
  {
    key: 'vectorized',
    label: '向量化',
    icon: '🔍',
    weight: 20,
    description: '将文本片段转换为向量表示'
  },
  {
    key: 'graph_built',
    label: '图谱构建',
    icon: '🕸️',
    weight: 20,
    description: '构建实体关系图谱'
  }
];

/**
 * 进度条组件
 */
const ProgressBar = ({ progress, status }) => {
  const getProgressColor = (status) => {
    const colorMap = {
      idle: '#8c8c8c',
      pending: '#fa8c16',
      queued: '#1890ff',
      processing: '#faad14',
      completed: '#52c41a',
      failed: '#ff4d4f',
      error: '#ff4d4f'
    };
    return colorMap[status] || '#8c8c8c';
  };

  return (
    <div className="progress-bar-container">
      <div 
        className="progress-bar-fill"
        style={{
          width: `${progress}%`,
          backgroundColor: getProgressColor(status)
        }}
      />
      <div className="progress-text">{Math.round(progress)}%</div>
    </div>
  );
};

/**
 * 阶段列表项组件
 */
const StageItem = ({ stage, completed, isActive, isLast }) => {
  return (
    <div 
      className={`stage-item ${completed ? 'completed' : ''} ${isActive ? 'active' : ''} ${isLast ? 'last' : ''}`}
      title={stage.description}
    >
      <div className="stage-icon-container">
        <span className="stage-icon">{stage.icon}</span>
        {completed && <span className="stage-check">✓</span>}
      </div>
      <div className="stage-info">
        <div className="stage-label">{stage.label}</div>
        <div className="stage-description">{stage.description}</div>
      </div>
      {!isLast && <div className="stage-arrow">→</div>}
    </div>
  );
};

/**
 * 文档进度追踪主组件
 */
const DocumentProgress = ({ document, showDetails = true }) => {
  if (!document) return null;

  const metadata = document.document_metadata || {};
  const processingStatus = metadata.processing_status || 'idle';

  // 计算完成进度
  const completedStages = PROCESSING_STAGES.filter(stage => metadata[stage.key] === true);
  const progress = (completedStages.length / PROCESSING_STAGES.length) * 100;

  // 如果不显示详细信息，只显示进度条
  if (!showDetails) {
    return (
      <div className="document-progress compact">
        <ProgressBar progress={progress} status={processingStatus} />
      </div>
    );
  }

  // 完整模式显示所有信息
  return (
    <div className="document-progress">
      {/* 总体进度 */}
      <div className="progress-overview">
        <div className="progress-header">
          <h4>文档处理进度</h4>
          <span className={`status-badge status-${processingStatus}`}>
            {getStatusText(processingStatus)}
          </span>
        </div>
        <ProgressBar progress={progress} status={processingStatus} />
        <div className="progress-stats">
          <span className="stat-item">
            已完成: {completedStages.length}/{PROCESSING_STAGES.length}
          </span>
          <span className="stat-item">
            总进度: {Math.round(progress)}%
          </span>
        </div>
      </div>

      {/* 详细阶段列表 */}
      <div className="stages-list">
        {PROCESSING_STAGES.map((stage, index) => {
          const isCompleted = metadata[stage.key] === true;
          const isActive = !isCompleted && index === completedStages.length;
          const isLast = index === PROCESSING_STAGES.length - 1;
          
          return (
            <StageItem
              key={stage.key}
              stage={stage}
              completed={isCompleted}
              isActive={isActive}
              isLast={isLast}
            />
          );
        })}
      </div>

      {/* 状态徽章 */}
      <div className="status-badge-section">
        <DocumentStatusBadge document={document} compact={false} />
      </div>
    </div>
  );
};

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    idle: '待处理',
    pending: '待处理',
    queued: '排队中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    error: '错误'
  };
  return statusMap[status] || status;
};

export default DocumentProgress;