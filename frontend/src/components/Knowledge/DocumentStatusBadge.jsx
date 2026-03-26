/**
 * 文档状态徽章组件
 * 
 * 用于显示文档处理的细粒度状态，包括文本提取、切片、实体识别、向量化、图谱构建等阶段
 */

import React from 'react';
import './DocumentStatusBadge.css';

/**
 * 处理阶段配置
 */
const PROCESSING_STAGES = [
  {
    key: 'text_extracted',
    label: '文本提取',
    icon: '📝',
    description: '从文档中提取文本内容'
  },
  {
    key: 'chunked',
    label: '切片处理',
    icon: '✂️',
    description: '将文本分割成适合向量化的片段'
  },
  {
    key: 'entity_extracted',
    label: '实体识别',
    icon: '🏷️',
    description: '识别文档中的命名实体'
  },
  {
    key: 'vectorized',
    label: '向量化',
    icon: '🔍',
    description: '将文本片段转换为向量表示'
  },
  {
    key: 'graph_built',
    label: '图谱构建',
    icon: '🕸️',
    description: '构建实体关系图谱'
  }
];

/**
 * 单个阶段徽章组件
 */
const StageBadge = ({ completed, label, icon, description, isLast }) => {
  return (
    <div 
      className={`stage-badge ${completed ? 'completed' : 'pending'} ${isLast ? 'last' : ''}`}
      title={description}
    >
      <div className="stage-icon">{icon}</div>
      <div className="stage-label">{label}</div>
      <div className="stage-indicator">
        {completed ? '✓' : '○'}
      </div>
      {!isLast && <div className="stage-connector" />}
    </div>
  );
};

/**
 * 文档状态徽章主组件
 */
const DocumentStatusBadge = ({ document, compact = false }) => {
  if (!document) return null;

  const metadata = document.document_metadata || {};
  const processingStatus = metadata.processing_status || 'idle';

  // 如果是紧凑模式，只显示总体状态
  if (compact) {
    return (
      <div className={`document-status-badge compact status-${processingStatus}`}>
        <span className="status-text">
          {getStatusText(processingStatus)}
        </span>
      </div>
    );
  }

  // 完整模式显示所有处理阶段
  return (
    <div className="document-status-badge">
      <div className="status-header">
        <span className="overall-status">
          总体状态: {getStatusText(processingStatus)}
        </span>
      </div>
      <div className="stages-container">
        {PROCESSING_STAGES.map((stage, index) => (
          <StageBadge
            key={stage.key}
            completed={isStageCompleted(processingStatus, stage.key)}
            label={stage.label}
            icon={stage.icon}
            description={stage.description}
            isLast={index === PROCESSING_STAGES.length - 1}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * 检查指定阶段是否已完成
 * @param {string} processingStatus - 当前处理状态
 * @param {string} stageKey - 阶段键
 * @returns {boolean} 是否完成
 */
const isStageCompleted = (processingStatus, stageKey) => {
  // 定义阶段的完成顺序
  const stageOrder = {
    'text_extracted': 1,
    'chunked': 2,
    'entity_extracted': 3,
    'vectorized': 4,
    'graph_built': 5
  };
  
  // 映射处理状态到阶段顺序
  const statusToStageOrder = {
    'text_extracted': 1,
    'text_extraction_failed': 1, // 失败状态也视为已完成该阶段
    'chunked': 2,
    'chunking_failed': 2,
    'entity_extracted': 3,
    'entities_extracted': 3, // 支持 entities_extracted 状态
    'entity_extraction_failed': 3,
    'entities_extraction_failed': 3, // 支持 entities_extraction_failed 状态
    'vectorized': 4,
    'vectorization_failed': 4,
    'graph_built': 5,
    'graph_building_failed': 5,
    'completed': 5, // 已完成所有阶段
    'failed': 5 // 最终失败状态
  };
  
  const currentStageOrder = statusToStageOrder[processingStatus] || 0;
  const targetStageOrder = stageOrder[stageKey] || 0;
  
  return currentStageOrder >= targetStageOrder;
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
    text_extracted: '已提取文本',
    text_extraction_failed: '文本提取失败',
    chunked: '已切片',
    chunking_failed: '切片失败',
    entity_extracted: '已识别实体',
    entities_extracted: '已识别实体', // 支持 entities_extracted 状态
    entity_extraction_failed: '实体识别失败',
    entities_extraction_failed: '实体识别失败', // 支持 entities_extraction_failed 状态
    vectorized: '已向量化',
    vectorization_failed: '向量化失败',
    graph_built: '已构建图谱',
    graph_building_failed: '图谱构建失败',
    completed: '已完成',
    failed: '失败',
    error: '错误'
  };
  return statusMap[status] || status;
};

export default DocumentStatusBadge;