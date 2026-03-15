/**
 * 处理中文档进度面板组件
 *
 * 显示正在处理的文档列表和进度信息
 */

import React from 'react';
import './ProcessingDocumentsPanel.css';

/**
 * 处理中文档进度面板组件
 *
 * @param {Object} props - 组件属性
 * @param {Map} props.processingDocuments - 正在处理的文档Map
 * @param {Map} props.processingProgress - 处理进度Map
 * @param {Object} props.queueStatus - 队列状态
 * @returns {JSX.Element} 进度面板
 */
const ProcessingDocumentsPanel = ({ processingDocuments, processingProgress, queueStatus }) => {
  if (processingDocuments.size === 0) {
    return null;
  }

  return (
    <div className="processing-documents-panel">
      <div className="processing-panel-header">
        <h4>📋 正在处理的文档 ({processingDocuments.size})</h4>
        {queueStatus && (
          <div className="queue-status-badge">
            <span className="queue-indicator"></span>
            队列: {queueStatus.processing_count} 处理中 / {queueStatus.queue_size} 等待中
          </div>
        )}
      </div>

      {/* 队列状态详情 */}
      {queueStatus && queueStatus.processing_documents && queueStatus.processing_documents.length > 0 && (
        <div className="queue-processing-info">
          <div className="queue-info-title">🔥 当前处理中:</div>
          {queueStatus.processing_documents.map((doc) => (
            <div key={doc.document_id} className="queue-processing-doc">
              <span className="doc-name">{doc.document_name}</span>
              <span className="doc-time">
                已处理: {Math.floor((Date.now() - new Date(doc.started_at).getTime()) / 1000 / 60)} 分钟
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="processing-list">
        {/* 使用state渲染处理中文档 */}
        {Array.from(processingDocuments.values()).map(({ id, name }) => {
          const progress = processingProgress.get(id);

          // 如果没有进度信息，显示默认状态
          if (!progress) {
            return (
              <div key={id} className="processing-item waiting">
                <div className="processing-header">
                  <span className="processing-name" title={name}>
                    {name.length > 30 ? name.substring(0, 30) + '...' : name}
                  </span>
                  <span className="processing-status">⏳ 等待中</span>
                </div>
                <div className="processing-progress-bar">
                  <div className="processing-progress-fill" style={{ width: '0%' }} />
                </div>
                <div className="processing-details">
                  <span className="processing-step">初始化中...</span>
                  <span className="processing-percent">0%</span>
                </div>
              </div>
            );
          }

          // 优先使用进度API的状态，而不是队列状态
          // 因为向量化可能通过后台线程直接启动，不在队列中
          const isActuallyProcessing = progress.status === 'processing';
          const isCompleted = progress.status === 'completed';
          const isFailed = progress.status === 'failed';

          // 获取队列位置信息（仅用于显示队列状态）
          const queuePosition = queueStatus?.processing_documents?.findIndex(
            doc => doc.document_id === id
          );
          const isInQueue = queuePosition !== -1 && queuePosition !== undefined;

          // 确定显示样式：实际处理中 > 在队列中 > 等待中
          const itemClass = isActuallyProcessing ? 'active' : (isInQueue ? 'queued' : 'waiting');

          return (
            <div key={id} className={`processing-item ${itemClass}`}>
              <div className="processing-header">
                <span className="processing-name" title={name}>
                  {name.length > 30 ? name.substring(0, 30) + '...' : name}
                </span>
                <span className={`processing-status ${progress.status}`}>
                  {isCompleted ? '✅ 完成' :
                   isFailed ? '❌ 失败' :
                   isActuallyProcessing ? '🔄 处理中' :
                   isInQueue ? '⏳ 队列中' : '⏳ 等待中'}
                </span>
              </div>

              {/* 队列位置提示 - 仅在不在队列中且不在处理中时显示 */}
              {!isInQueue && !isActuallyProcessing && queueStatus && (
                <div className="queue-position-hint">
                  在队列中等待处理...
                </div>
              )}

              <div className="processing-progress-bar">
                <div
                  className={`processing-progress-fill ${progress.status}`}
                  style={{ width: `${progress.progress_percentage || progress.progress_percent || 0}%` }}
                />
              </div>
              <div className="processing-details">
                <span className="processing-step">{progress.step_name}</span>
                <span className="processing-percent">{progress.progress_percentage || progress.progress_percent || 0}%</span>
              </div>
              {progress.message && (
                <div className="processing-message">{progress.message}</div>
              )}
              {progress.status === 'processing' && progress.batch && (
                <div className="batch-progress">
                  批次: {progress.batch}/{progress.total_batches}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProcessingDocumentsPanel;
